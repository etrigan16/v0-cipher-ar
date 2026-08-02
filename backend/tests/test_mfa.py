"""MFA flow tests: rate limiter, setup, verify, challenge, login MFA, disable,
partial token rejection.

Follows the same test patterns as test_auth.py: in-memory SQLite via conftest.
"""

import time

import pytest

from app.utils.rate_limiter import InMemoryRateLimiter


# ── Unit tests for InMemoryRateLimiter ─────────────────────────────────────

class TestRateLimiter:
    def test_allows_within_limit(self):
        limiter = InMemoryRateLimiter(max_attempts=3, window_seconds=60)
        assert limiter.check("key1") is True
        limiter.record("key1")
        assert limiter.check("key1") is True
        limiter.record("key1")
        assert limiter.check("key1") is True
        limiter.record("key1")
        # 3 attempts used, should still be allowed on the 3rd check since
        # check() returns True when count < max (3 < 3 = False → blocked)
        # Actually after 3 records, the next check should be false.
        # Let's be precise: after 3 records, len([t1,t2,t3]) == 3, so
        # check returns 3 < 3 → False.
        assert limiter.check("key1") is False

    def test_blocks_at_limit(self):
        limiter = InMemoryRateLimiter(max_attempts=2, window_seconds=60)
        limiter.record("k")
        limiter.record("k")
        assert limiter.check("k") is False

    def test_resets_after_window(self):
        limiter = InMemoryRateLimiter(max_attempts=1, window_seconds=0.05)
        limiter.record("k")
        assert limiter.check("k") is False
        time.sleep(0.06)
        assert limiter.check("k") is True

    def test_independent_keys(self):
        limiter = InMemoryRateLimiter(max_attempts=2, window_seconds=60)
        limiter.record("a")
        limiter.record("a")
        limiter.record("b")
        assert limiter.check("a") is False
        assert limiter.check("b") is True

    def test_raise_if_limited(self):
        limiter = InMemoryRateLimiter(max_attempts=1, window_seconds=60)
        limiter.record("x")
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            limiter.raise_if_limited("x")
        assert exc.value.status_code == 429


# ── Fixture helpers ────────────────────────────────────────────────────────

async def _register_user(client, email: str, password: str = "secret123",
                         name: str = "Test User") -> dict:
    resp = await client.post("/auth/register", json={
        "email": email, "password": password, "name": name,
    })
    return resp.json()


async def _login_full(client, email: str, password: str = "secret123") -> str:
    """Login and return a full access token (non-MFA user)."""
    resp = await client.post("/auth/login", json={
        "email": email, "password": password,
    })
    return resp.json()["access_token"]


# ── Integration tests ──────────────────────────────────────────────────────

class TestMfaSetup:
    async def test_setup_returns_secret_and_uri(self, client):
        email = "setup1@example.com"
        await _register_user(client, email)
        token = await _login_full(client, email)

        resp = await client.post(
            "/auth/mfa/setup",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "secret" in body
        assert "provisioning_uri" in body
        assert body["provisioning_uri"].startswith("otpauth://totp/")
        assert "AUKALABS" in body["provisioning_uri"]

    async def test_setup_rejects_partial_token(self, client):
        """Partial tokens should be rejected by setup (via get_current_user)."""
        email = "setup2@example.com"
        await _register_user(client, email)
        # Enable MFA first
        token = await _login_full(client, email)
        resp = await client.post("/auth/mfa/setup",
                                 headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        secret = resp.json()["secret"]

        # Enable MFA
        import pyotp
        totp = pyotp.TOTP(secret)
        code = totp.now()
        await client.post("/auth/mfa/verify",
                          json={"code": code},
                          headers={"Authorization": f"Bearer {token}"})

        # Now login to get a partial token
        login_resp = await client.post("/auth/login", json={
            "email": email, "password": "secret123",
        })
        partial = login_resp.json()["partial_token"]

        resp = await client.post(
            "/auth/mfa/setup",
            headers={"Authorization": f"Bearer {partial}"},
        )
        assert resp.status_code == 401


class TestMfaVerify:
    async def test_verify_valid_code_enables_mfa(self, client):
        email = "verify1@example.com"
        await _register_user(client, email)
        token = await _login_full(client, email)

        # setup
        setup = await client.post("/auth/mfa/setup",
                                  headers={"Authorization": f"Bearer {token}"})
        secret = setup.json()["secret"]

        import pyotp
        totp = pyotp.TOTP(secret)
        code = totp.now()

        resp = await client.post("/auth/mfa/verify",
                                 json={"code": code},
                                 headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["detail"] == "MFA activado correctamente"

    async def test_verify_invalid_code_returns_400(self, client):
        email = "verify2@example.com"
        await _register_user(client, email)
        token = await _login_full(client, email)

        await client.post("/auth/mfa/setup",
                          headers={"Authorization": f"Bearer {token}"})

        resp = await client.post("/auth/mfa/verify",
                                 json={"code": "000000"},
                                 headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 400

    async def test_verify_without_setup_returns_400(self, client):
        email = "verify3@example.com"
        await _register_user(client, email)
        token = await _login_full(client, email)

        resp = await client.post("/auth/mfa/verify",
                                 json={"code": "123456"},
                                 headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 400


class TestMfaChallenge:
    async def test_challenge_valid_code_returns_full_token(self, client):
        email = "chal1@example.com"
        await _register_user(client, email)
        token = await _login_full(client, email)

        # setup + verify
        setup = await client.post("/auth/mfa/setup",
                                  headers={"Authorization": f"Bearer {token}"})
        secret = setup.json()["secret"]
        import pyotp
        totp = pyotp.TOTP(secret)
        await client.post("/auth/mfa/verify",
                          json={"code": totp.now()},
                          headers={"Authorization": f"Bearer {token}"})

        # login → partial token
        login_resp = await client.post("/auth/login", json={
            "email": email, "password": "secret123",
        })
        partial = login_resp.json()["partial_token"]

        # challenge with valid TOTP
        resp = await client.post("/auth/mfa/challenge", json={
            "partial_token": partial,
            "code": totp.now(),
        })
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    async def test_challenge_invalid_code_returns_401(self, client):
        email = "chal2@example.com"
        await _register_user(client, email)
        token = await _login_full(client, email)

        setup = await client.post("/auth/mfa/setup",
                                  headers={"Authorization": f"Bearer {token}"})
        secret = setup.json()["secret"]
        import pyotp
        totp = pyotp.TOTP(secret)
        await client.post("/auth/mfa/verify",
                          json={"code": totp.now()},
                          headers={"Authorization": f"Bearer {token}"})

        login_resp = await client.post("/auth/login", json={
            "email": email, "password": "secret123",
        })
        partial = login_resp.json()["partial_token"]

        resp = await client.post("/auth/mfa/challenge", json={
            "partial_token": partial,
            "code": "000000",
        })
        assert resp.status_code == 401


class TestMfaLoginFlow:
    async def test_mfa_enabled_returns_partial_token(self, client):
        email = "login1@example.com"
        await _register_user(client, email)
        token = await _login_full(client, email)

        # setup + verify MFA
        setup = await client.post("/auth/mfa/setup",
                                  headers={"Authorization": f"Bearer {token}"})
        secret = setup.json()["secret"]
        import pyotp
        totp = pyotp.TOTP(secret)
        await client.post("/auth/mfa/verify",
                          json={"code": totp.now()},
                          headers={"Authorization": f"Bearer {token}"})

        # login now should return partial_token
        resp = await client.post("/auth/login", json={
            "email": email, "password": "secret123",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert "partial_token" in body
        assert body.get("mfa_required") is True
        assert "access_token" not in body

    async def test_mfa_disabled_returns_full_token(self, client):
        email = "login2@example.com"
        await _register_user(client, email)

        resp = await client.post("/auth/login", json={
            "email": email, "password": "secret123",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "partial_token" not in body


class TestMfaDisable:
    async def test_disable_with_correct_password(self, client):
        email = "disable1@example.com"
        await _register_user(client, email)
        token = await _login_full(client, email)

        # setup + verify
        setup = await client.post("/auth/mfa/setup",
                                  headers={"Authorization": f"Bearer {token}"})
        secret = setup.json()["secret"]
        import pyotp
        totp = pyotp.TOTP(secret)
        await client.post("/auth/mfa/verify",
                          json={"code": totp.now()},
                          headers={"Authorization": f"Bearer {token}"})

        # disable
        resp = await client.post("/auth/mfa/disable",
                                 json={"password": "secret123"},
                                 headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["detail"] == "MFA desactivado correctamente"

        # login should now return full token (MFA disabled)
        login_resp = await client.post("/auth/login", json={
            "email": email, "password": "secret123",
        })
        assert "access_token" in login_resp.json()

    async def test_disable_with_wrong_password_returns_401(self, client):
        email = "disable2@example.com"
        await _register_user(client, email)
        token = await _login_full(client, email)

        setup = await client.post("/auth/mfa/setup",
                                  headers={"Authorization": f"Bearer {token}"})
        import pyotp
        totp = pyotp.TOTP(setup.json()["secret"])
        await client.post("/auth/mfa/verify",
                          json={"code": totp.now()},
                          headers={"Authorization": f"Bearer {token}"})

        resp = await client.post("/auth/mfa/disable",
                                 json={"password": "wrongpassword"},
                                 headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401

    async def test_disable_when_already_disabled_returns_400(self, client):
        email = "disable3@example.com"
        await _register_user(client, email)
        token = await _login_full(client, email)

        resp = await client.post("/auth/mfa/disable",
                                 json={"password": "secret123"},
                                 headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 400


class TestPartialTokenRejection:
    async def test_protected_endpoint_rejects_partial_token(self, client):
        """get_current_user should reject tokens with mfa_challenge claim."""
        email = "reject1@example.com"
        await _register_user(client, email)
        token = await _login_full(client, email)

        # Enable MFA to get a partial token
        setup = await client.post("/auth/mfa/setup",
                                  headers={"Authorization": f"Bearer {token}"})
        import pyotp
        totp = pyotp.TOTP(setup.json()["secret"])
        await client.post("/auth/mfa/verify",
                          json={"code": totp.now()},
                          headers={"Authorization": f"Bearer {token}"})

        login_resp = await client.post("/auth/login", json={
            "email": email, "password": "secret123",
        })
        partial = login_resp.json()["partial_token"]

        # Try /auth/me with partial token
        resp = await client.get("/auth/me",
                                headers={"Authorization": f"Bearer {partial}"})
        assert resp.status_code == 401


class TestMfaChallengeRateLimit:
    async def test_rate_limit_exceeded_returns_429(self, client):
        """6th attempt with the same partial token should return 429."""
        email = "ratelimit1@example.com"
        await _register_user(client, email)
        token = await _login_full(client, email)

        # setup + verify
        setup = await client.post("/auth/mfa/setup",
                                  headers={"Authorization": f"Bearer {token}"})
        import pyotp
        totp = pyotp.TOTP(setup.json()["secret"])
        await client.post("/auth/mfa/verify",
                          json={"code": totp.now()},
                          headers={"Authorization": f"Bearer {token}"})

        # login → partial token
        login_resp = await client.post("/auth/login", json={
            "email": email, "password": "secret123",
        })
        partial = login_resp.json()["partial_token"]

        # 5 attempts with wrong code
        for _ in range(5):
            resp = await client.post("/auth/mfa/challenge", json={
                "partial_token": partial,
                "code": "000000",
            })
            assert resp.status_code == 401  # invalid code, not rate-limited yet

        # 6th attempt should be rate-limited
        resp = await client.post("/auth/mfa/challenge", json={
            "partial_token": partial,
            "code": "000000",
        })
        assert resp.status_code == 429
