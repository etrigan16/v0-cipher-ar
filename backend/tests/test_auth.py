"""Auth flow tests: register, login and /auth/me against the SQLite test app.

RED test note (task 3.3): `test_me_with_valid_token` expects the JWT ``sub``
(string) to match the user id. With a non-portable UUID type this fails, which
is the str->UUID coercion gap the green flip (task 3.4) closes. Emails are
unique per test to avoid duplicate-key cross-talk (design D5).
"""


async def test_register_success(client):
    resp = await client.post(
        "/auth/register",
        json={
            "email": "alice@example.com",
            "password": "secret123",
            "name": "Alice",
            "company_name": "Alice Corp",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "alice@example.com"
    assert body["name"] == "Alice"
    assert body["id"]
    assert body["tenant"] is not None
    assert body["tenant"]["id"]
    assert body["tenant"]["slug"] == "alice-corp"


async def test_register_missing_company_name(client):
    """422 when company_name is missing."""
    resp = await client.post(
        "/auth/register",
        json={"email": "no-company@example.com", "password": "secret123", "name": "NoCo"},
    )
    assert resp.status_code == 422


async def test_register_duplicate_email(client):
    payload = {
        "email": "dup@example.com",
        "password": "secret123",
        "name": "Dup",
        "company_name": "Dup Corp",
    }
    first = await client.post("/auth/register", json=payload)
    assert first.status_code == 201
    second = await client.post("/auth/register", json=payload)
    assert second.status_code == 400


async def test_login_success(client):
    email = "bob@example.com"
    await client.post(
        "/auth/register",
        json={"email": email, "password": "secret123", "name": "Bob", "company_name": "Bob Inc"},
    )
    resp = await client.post("/auth/login", json={"email": email, "password": "secret123"})
    assert resp.status_code == 200
    assert resp.json()["access_token"]


async def test_login_bad_credentials(client):
    email = "carol@example.com"
    await client.post(
        "/auth/register",
        json={"email": email, "password": "secret123", "name": "Carol", "company_name": "Carol Ltd"},
    )
    resp = await client.post("/auth/login", json={"email": email, "password": "wrong"})
    assert resp.status_code == 401


async def test_me_with_valid_token(client):
    email = "dave@example.com"
    await client.post(
        "/auth/register",
        json={"email": email, "password": "secret123", "name": "Dave", "company_name": "Dave Co"},
    )
    login = await client.post("/auth/login", json={"email": email, "password": "secret123"})
    token = login.json()["access_token"]
    resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == email
    assert body["tenant"] is not None
    assert body["tenant"]["slug"] == "dave-co"


async def test_me_with_invalid_token(client):
    resp = await client.get(
        "/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert resp.status_code == 401


async def test_login_returns_jwt_with_tenant_id(client):
    """Login JWT includes tenant_id claim."""
    email = "frank@example.com"
    await client.post(
        "/auth/register",
        json={"email": email, "password": "secret123", "name": "Frank", "company_name": "Frank GmbH"},
    )
    resp = await client.post("/auth/login", json={"email": email, "password": "secret123"})
    token = resp.json()["access_token"]
    # Decode the token with the test secret to inspect claims
    from jose import jwt as jose_jwt

    payload = jose_jwt.decode(
        token,
        "test-secret",
        algorithms=["HS256"],
    )
    assert "tenant_id" in payload
    assert payload["tenant_id"] is not None
