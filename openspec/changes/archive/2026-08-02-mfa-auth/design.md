# Design: MFA / TOTP Authentication

## Technical Approach

Two-step login via partial JWT tokens. After password verification, if `user.mfa_enabled` is true, login returns a short-lived JWT (5 min, `mfa_challenge: true` claim) instead of a full session token. The client presents this partial token + TOTP code to `/auth/mfa/challenge` to exchange for a full JWT. `get_current_user` rejects all tokens carrying `mfa_challenge`. Non-MFA users see zero change.

Backend: pyotp for TOTP generation and verification. In-memory dict for rate limiting on challenge. Frontend: auth-context adds `mfaChallenge` state; login page renders conditional TOTP step; new `/dashboard/mfa` page for setup.

## Architecture Decisions

| Decision | Options | Rationale |
|---|---|---|
| Partial token: JWT claim vs opaque DB token | JWT claim `mfa_challenge: true` vs stored challenge in DB | JWT requires no DB write, no cleanup of expired challenges. The claim is verified by `get_current_user` in the existing decode path. |
| Rate limiter: in-memory dict vs Redis | Dict (dict[str, list[float]]) vs Redis | 5-min token window makes Redis overkill. A single dict scoped to the challenge endpoint is sufficient for current scale. Trivially replaceable with Redis later. |
| TOTP lib: pyotp vs onetimepass | pyotp vs onetimepass | pyotp is actively maintained, has `random_base32()` and `provisioning_uri()` built in, single dependency. |
| MFA secret storage: plaintext vs encrypted | Plaintext column vs encrypted at rest | Acceptable for current scope. Encryption wrapper can be added later without schema migration. |
| Setup regeneration: reset vs error on re-setup | Regenerate secret, keep disabled until verify vs return error | User may lose the QR code before verifying. Regeneration is safer UX. |

## Data Flow

```
Login (password correct)
  ├─ user.mfa_enabled == False → Full JWT (1440 min)
  └─ user.mfa_enabled == True  → Partial JWT (5 min, mfa_challenge: true)

Challenge (partial JWT + TOTP)
  ├─ Rate limit exceeded       → 429
  ├─ Invalid TOTP              → 401 + increment attempt count
  └─ Valid TOTP                → Full JWT (1440 min)

Protected endpoint
  ├─ Token has mfa_challenge   → 401
  └─ Normal token              → return
```

## File Changes

| File | Action | Description |
|---|---|---|
| `backend/app/models/user.py` | Modify | Add `mfa_secret` (nullable String), `mfa_enabled` (Boolean, default False) |
| `backend/app/routes/auth.py` | Modify | Login: check `mfa_enabled` → return partial token. `get_current_user`: reject `mfa_challenge` tokens. Add `create_partial_token()` |
| `backend/app/routes/mfa.py` | Create | 4 routes: setup, verify, disable, challenge |
| `backend/app/routes/rate_limiter.py` | Create | In-memory dict limiter (max 5/min per partial token) |
| `backend/app/main.py` | Modify | Register `mfa.router` |
| `backend/requirements.txt` | Modify | Add `pyotp` |
| `backend/tests/test_mfa.py` | Create | ~15 backend MFA scenarios |
| `lib/api.ts` | Modify | Add `api.auth.mfa` namespace |
| `components/auth-context.tsx` | Modify | Add `mfaChallenge` state (null \| {partialToken, email}), two-step login |
| `app/login/page.tsx` | Modify | Conditional TOTP input when `mfaChallenge` present |
| `app/dashboard/mfa/page.tsx` | Create | QR code display, TOTP verify, disable with password |
| `app/dashboard/layout.tsx` | Modify | Add MFA sidebar link |

## Interfaces / Contracts

```python
# Partial token response (login when MFA enabled)
class PartialTokenResponse(BaseModel):
    partial_token: str
    token_type: str = "bearer"
    mfa_required: bool = True

# Setup response
class MfaSetupResponse(BaseModel):
    secret: str
    provisioning_uri: str

# Verify request
class MfaVerifyRequest(BaseModel):
    code: str  # 6-digit TOTP

# Disable request
class MfaDisableRequest(BaseModel):
    password: str

# Challenge request
class MfaChallengeRequest(BaseModel):
    partial_token: str
    code: str
```

```python
# Rate limiter
class InMemoryRateLimiter:
    _store: dict[str, list[float]]  # key → [timestamps]
    max_attempts: int = 5
    window_seconds: int = 60
    def check(key: str) -> bool
    def record(key: str) -> None
```

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Unit | Rate limiter (limit hit, window expiry, reset) | Direct instantiation, assert block/release |
| Integration | Setup → verify → challenge flow; wrong codes; expired partial tokens; full token on challenge | httpx AsyncClient against SQLite test app (existing conftest.py pattern) |
| Integration | `get_current_user` rejects partial tokens | GET /auth/me with partial token → 401 |
| Integration | Login backward compat | Non-MFA user login returns access_token only |
| Frontend | Login page TOTP input conditional render | vitest + RTL mock fetch responses |

## Threat Matrix

N/A — no shell command, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary. The change adds HTTP API routes only, which is not a routing type covered by the threat matrix.

## Migration / Rollout

No data migration required. `mfa_secret` is nullable (default NULL), `mfa_enabled` defaults to False via SQLAlchemy `server_default`. Existing JWT tokens remain valid — they lack the `mfa_challenge` claim so `get_current_user` behavior is unchanged.

## Open Questions

- [ ] Should setup regenerate the QR every time it's called, or only when no pending unverified secret exists? Current design: regenerate always.
