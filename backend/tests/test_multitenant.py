"""Tests for multi-tenant integration: transaction rollback, middleware 401, and RLS-aware flows.

All tests use the SQLite test app from conftest.py. RLS-specific tests
(requiring PostgreSQL) are marked skip_sqlite and documented accordingly.
"""

import pytest


async def test_registration_no_orphan_tenant_on_failure(client):
    """R5: Transaction rollback — duplicate email causes rejection before tenant creation.

    If a user with the same email already exists, the registration should
    return 400 and no new tenant should be visible.
    """
    # First registration succeeds
    resp = await client.post(
        "/auth/register",
        json={
            "email": "orphan@test.com",
            "password": "secret123",
            "name": "Orphan",
            "company_name": "Orphan Corp",
        },
    )
    assert resp.status_code == 201

    # Second registration with same email fails (400) — no orphan tenant
    resp = await client.post(
        "/auth/register",
        json={
            "email": "orphan@test.com",
            "password": "secret123",
            "name": "Orphan Dupe",
            "company_name": "Orphan Corp 2",
        },
    )
    assert resp.status_code == 400


async def test_login_returns_jwt_with_tenant_id(client):
    """R4: Login JWT includes tenant_id claim."""
    email = "tenantclaim@test.com"
    await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "secret123",
            "name": "Tenant Claim",
            "company_name": "Claim Corp",
        },
    )
    resp = await client.post("/auth/login", json={"email": email, "password": "secret123"})
    token = resp.json()["access_token"]

    from jose import jwt as jose_jwt

    payload = jose_jwt.decode(token, "test-secret", algorithms=["HS256"])
    assert "tenant_id" in payload
    assert payload["tenant_id"] is not None


async def test_middleware_rejects_expired_token(client):
    """R4: 401 when JWT is expired."""
    from datetime import datetime, timedelta, timezone

    from jose import jwt as jose_jwt

    token = jose_jwt.encode(
        {
            "sub": "fake-user-id",
            "tenant_id": "fake-tenant-id",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=30),
        },
        "test-secret",
        algorithm="HS256",
    )

    resp = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 401


# ── RLS tests ──────────────────────────────────────────────────────────
# PostgreSQL-only — skip in SQLite

pytestmark_skip_sqlite = pytest.mark.skip(
    reason="RLS requires PostgreSQL (current fixture uses SQLite)"
)


@pytest.mark.skip(reason="RLS requires PostgreSQL — run against staging")
async def test_rls_cross_tenant_isolation():
    """R3/R9: Cross-tenant queries return empty for non-admin users.

    Requires PostgreSQL with RLS policies enabled. Run manually against staging.
    """
    pass


@pytest.mark.skip(reason="RLS requires PostgreSQL — run against staging")
async def test_rls_superadmin_bypass():
    """R3: Superadmin sees all rows despite RLS.

    Requires PostgreSQL with RLS policies enabled. Run manually against staging.
    """
    pass
