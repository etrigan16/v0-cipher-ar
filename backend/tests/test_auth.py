"""Auth flow tests: register, login and /auth/me against the SQLite test app.

RED test note (task 3.3): `test_me_with_valid_token` expects the JWT ``sub``
(string) to match the user id. With a non-portable UUID type this fails, which
is the str->UUID coercion gap the green flip (task 3.4) closes. Emails are
unique per test to avoid duplicate-key cross-talk (design D5).
"""


async def test_register_success(client):
    resp = await client.post(
        "/auth/register",
        json={"email": "alice@example.com", "password": "secret123", "name": "Alice"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "alice@example.com"
    assert body["name"] == "Alice"
    assert body["id"]


async def test_register_duplicate_email(client):
    payload = {"email": "dup@example.com", "password": "secret123", "name": "Dup"}
    first = await client.post("/auth/register", json=payload)
    assert first.status_code == 201
    second = await client.post("/auth/register", json=payload)
    assert second.status_code == 400


async def test_login_success(client):
    email = "bob@example.com"
    await client.post(
        "/auth/register",
        json={"email": email, "password": "secret123", "name": "Bob"},
    )
    resp = await client.post("/auth/login", json={"email": email, "password": "secret123"})
    assert resp.status_code == 200
    assert resp.json()["access_token"]


async def test_login_bad_credentials(client):
    email = "carol@example.com"
    await client.post(
        "/auth/register",
        json={"email": email, "password": "secret123", "name": "Carol"},
    )
    resp = await client.post("/auth/login", json={"email": email, "password": "wrong"})
    assert resp.status_code == 401


async def test_me_with_valid_token(client):
    email = "dave@example.com"
    await client.post(
        "/auth/register",
        json={"email": email, "password": "secret123", "name": "Dave"},
    )
    login = await client.post("/auth/login", json={"email": email, "password": "secret123"})
    token = login.json()["access_token"]
    resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == email


async def test_me_with_invalid_token(client):
    resp = await client.get(
        "/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert resp.status_code == 401
