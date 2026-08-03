"""Waitlist API tests: 10 scenarios covering R1–R8.

Cooldown dict is imported and cleared between tests to avoid cross-talk.
send_confirmation_email is monkeypatched so tests never call Resend.
"""

from unittest.mock import AsyncMock

import pytest
import pytest_asyncio

from app.main import app


@pytest_asyncio.fixture(autouse=True)
async def _clear_cooldown():
    """Clear the in-memory cooldown dict before each test."""
    from app.routes.waitlist import _cooldown

    _cooldown.clear()
    yield


@pytest_asyncio.fixture(autouse=True)
async def _mock_resend(monkeypatch):
    """Monkeypatch send_confirmation_email to a no-op AsyncMock."""

    async def noop_email(_user_email: str) -> None:
        return None

    monkeypatch.setattr(
        "app.routes.waitlist.send_confirmation_email",
        AsyncMock(side_effect=noop_email),
    )


async def test_create_waitlist_entry_valid_email(client):
    """R1/R2: 201 on valid email (no company)."""
    resp = await client.post(
        "/api/v1/waitlist",
        json={"email": "alice@example.com"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "alice@example.com"
    assert body["company"] is None
    assert body["id"]
    assert body["created_at"]


async def test_create_waitlist_entry_with_company(client):
    """R1/R2: 201 on valid email with optional company."""
    resp = await client.post(
        "/api/v1/waitlist",
        json={"email": "bob@acme.com", "company": "Acme Corp"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "bob@acme.com"
    assert body["company"] == "Acme Corp"


async def test_create_waitlist_missing_email(client):
    """R2: 422 on missing email field."""
    resp = await client.post(
        "/api/v1/waitlist",
        json={"company": "No Email Inc"},
    )
    assert resp.status_code == 422


async def test_create_waitlist_invalid_email_format(client):
    """R2/R6: 422 on malformed email string -> Pydantic EmailStr rejects it."""
    resp = await client.post(
        "/api/v1/waitlist",
        json={"email": "not-an-email"},
    )
    assert resp.status_code == 422


async def test_create_waitlist_duplicate_email(client):
    """R7: 409 on duplicate email (unique constraint)."""
    from app.routes.waitlist import _cooldown

    email = "dup@example.com"
    first = await client.post(
        "/api/v1/waitlist",
        json={"email": email},
    )
    assert first.status_code == 201

    # Clear cooldown so the second request reaches the duplicate check
    _cooldown.pop(email, None)

    second = await client.post(
        "/api/v1/waitlist",
        json={"email": email},
    )
    assert second.status_code == 409
    body = second.json()
    assert "detail" in body


async def test_create_waitlist_rate_limited(client):
    """R4: 429 when same email submits within 5 minutes."""
    email = "ratelimit@example.com"
    # First submission succeeds and sets cooldown
    first = await client.post(
        "/api/v1/waitlist",
        json={"email": email},
    )
    assert first.status_code == 201

    # Second submission immediately after -> 429
    second = await client.post(
        "/api/v1/waitlist",
        json={"email": email},
    )
    assert second.status_code == 429
    body = second.json()
    assert "detail" in body
    # Verify retry-after header
    assert "retry-after" in second.headers


async def test_create_waitlist_cooldown_expired(client):
    """R4: 201 when cooldown has expired (>= 5 min since last attempt)."""
    from datetime import datetime, timezone

    from app.routes.waitlist import _cooldown

    email = "expired@example.com"
    # Manually set cooldown to 6 minutes ago
    _cooldown[email] = datetime.now(timezone.utc).timestamp() - 360  # 6 min

    resp = await client.post(
        "/api/v1/waitlist",
        json={"email": email},
    )
    assert resp.status_code == 201


async def test_resend_sends_on_success(client):
    """R3: Confirmation email is sent (via mock) on successful creation."""
    from app.routes.waitlist import send_confirmation_email

    send_confirmation_email.reset_mock()

    resp = await client.post(
        "/api/v1/waitlist",
        json={"email": "notify@example.com"},
    )
    assert resp.status_code == 201
    send_confirmation_email.assert_awaited_once_with("notify@example.com")


async def test_resend_failure_still_returns_201(client):
    """R3: 201 + warning logged when Resend fails (fire-and-forget)."""
    from app.routes.waitlist import send_confirmation_email

    send_confirmation_email.reset_mock()

    async def failing_email(_email: str) -> None:
        raise RuntimeError("Resend API unreachable")

    send_confirmation_email.side_effect = failing_email

    resp = await client.post(
        "/api/v1/waitlist",
        json={"email": "resendfail@example.com"},
    )
    assert resp.status_code == 201


async def test_database_failure_returns_500(client, monkeypatch):
    """R8: 500 when DB commit fails."""
    from unittest.mock import AsyncMock

    from app.database import get_db

    # Mock the session so commit raises
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=AsyncMock(scalar_one_or_none=lambda: None))
    mock_session.commit.side_effect = Exception("DB connection lost")
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None

    async def broken_db():
        yield mock_session

    # Override the FastAPI dependency for this test
    app.dependency_overrides[get_db] = broken_db

    try:
        resp = await client.post(
            "/api/v1/waitlist",
            json={"email": "dbfail@example.com"},
        )
        assert resp.status_code == 500
        body = resp.json()
        assert "detail" in body
    finally:
        app.dependency_overrides.pop(get_db, None)
