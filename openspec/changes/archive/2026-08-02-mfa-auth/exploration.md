## Exploration: MFA / TOTP Authentication

### Current State

The current auth system is password-only with single JWT tokens:

**Backend** (`backend/app/routes/auth.py`):
- `POST /auth/register` — creates user with bcrypt-hashed password
- `POST /auth/login` — validates email+password, returns JWT (HS256, 1440 min expiry)
- `GET /auth/me` — validates Bearer token via `get_current_user` dependency
- JWT payload: `{ sub: user_id (string), exp: timestamp }` — no partial tokens, no MFA claims
- `create_access_token()` encodes the JWT; `get_current_user()` decodes and queries DB
- No MFA routes, no MFA logic anywhere

**User Model** (`backend/app/models/user.py`):
- `id` (CoercingUuid primary key), `email` (unique, indexed), `name`, `hashed_password`, `is_active`, `created_at`
- **NO** `mfa_secret`, **NO** `mfa_enabled` fields

**Configuration** (`backend/app/config.py`):
- `secret_key` (required, from env), `algorithm` (HS256), `access_token_expire_minutes` (1440)

**Dependencies** (`backend/requirements.txt`):
- `python-jose[cryptography]` for JWT, `passlib[bcrypt]` + `bcrypt` for passwords
- **pyotp NOT installed** — must be added

**Frontend**:
- `lib/api.ts` — `api.auth.login()`, `api.auth.register()`, `api.auth.me()` — uses localStorage for JWT
- `components/auth-context.tsx` — `AuthProvider` manages user/token state. `login()` stores token, immediately calls `/auth/me`
- `app/login/page.tsx` — simple email+password form, stores token on success, redirects to `/dashboard`
- `app/dashboard/layout.tsx` — protected layout, redirects to `/login` if no user
- `components/ui/input-otp.tsx` — shadcn OTP input component already exists (reusable for TOTP entry)
- **No settings/profile page** exists — MFA setup needs a new page

**Tests** (`backend/tests/test_auth.py`): 6 tests (register success/duplicate, login success/bad creds, /auth/me valid/invalid token). No MFA tests. Conftest uses SQLite in-memory.

### Affected Areas

- `backend/app/models/user.py` — Add `mfa_secret` (nullable String), `mfa_enabled` (Boolean default False)
- `backend/app/routes/auth.py` — Modify `create_access_token` (support partial tokens), modify `login` (return partial token when MFA enabled), modify `get_current_user` (reject partial tokens)
- `backend/app/routes/mfa.py` — New file: setup, verify, disable, challenge routes
- `backend/app/main.py` — Register new `mfa.router`
- `backend/requirements.txt` — Add `pyotp`
- `backend/.env.example` — No changes needed (pyotp has no config required)
- `backend/tests/test_auth.py` — Add MFA scenarios
- `backend/tests/conftest.py` — No changes needed
- `lib/api.ts` — Add `api.auth.mfa` namespace (setup, verify, disable, challenge)
- `components/auth-context.tsx` — Add `mfaChallenge` state, two-step login flow
- `app/login/page.tsx` — Add MFA challenge step after password verification
- `app/dashboard/mfa/page.tsx` — New page: MFA setup (QR code + verify + disable)
- `app/dashboard/layout.tsx` — Add MFA settings link to sidebar
- `components/ui/input-otp.tsx` — Already exists, reusable as-is

### Approaches

1. **Two-step login with partial tokens (recommended)**
   - Login returns partial token (`sub` + `mfa_challenge: true`, 5 min expiry) when MFA is enabled
   - Client presents partial token + TOTP code to `/auth/mfa/challenge` → full JWT
   - `get_current_user` explicitly rejects tokens with `mfa_challenge: true`
   - New routes in `mfa.py`: setup (generate secret + QR URI), verify (confirm TOTP, enable), disable (turn off), challenge (partial→full)
   - Frontend: login flow splits into password step → MFA challenge step
   - Pros: Minimal UX change for non-MFA users, standard pattern, backward compatible
   - Cons: Adds login state complexity on frontend, partial token window is a small attack surface
   - Effort: Medium

2. **Full JWT with MFA claim (all-at-once)**
   - Login always returns full JWT regardless of MFA status
   - JWT includes `mfa_verified: false` claim
   - Some endpoints (like /auth/me) check the claim and reject unverified tokens
   - Client must call challenge endpoint to verify MFA and get a new JWT with `mfa_verified: true`
   - Pros: Single token model, simpler `get_current_user` logic
   - Cons: Less standard, every guarded endpoint needs the MFA claim check, breaks mid-session if user's MFA state changes
   - Effort: Medium

3. **Separate MFA session token**
   - Login always returns a short-lived session token (5 min, no MFA distinction)
   - Client must call challenge endpoint to exchange for a full JWT
   - All users go through two-step login
   - Pros: Uniform UX, no MFA state in token
   - Cons: Adds friction for non-MFA users, breaks current login flow for everyone
   - Effort: Medium

### Recommendation

**Approach 1 (Two-step login with partial tokens)** is recommended because:

1. **Zero impact on non-MFA users** — they get a full JWT on login as today
2. **Standard pattern** — used by major platforms (GitHub, Google, AWS)
3. **Small, focused changes** — only `get_current_user` and `login` in auth.py; new mfa.py module
4. **Partial token safety** — 5 min expiry + explicit claim check prevents misuse
5. **Reusable shadcn component** — `input-otp` already exists, no new UI primitives needed

### Detailed Design Sketch

**Model changes** (User model):
```
mfa_secret: Column(String, nullable=True)     # encrypted TOTP secret
mfa_enabled: Column(Boolean, default=False)   # whether MFA is active
```

**New routes** (`backend/app/routes/mfa.py`):
- `POST /auth/mfa/setup` — Requires auth, generates `pyotp.totp.TOTP` secret + provisioning URI, returns secret + qrcode data URL
- `POST /auth/mfa/verify` — Requires auth, takes TOTP code, validates against stored secret, enables MFA
- `POST /auth/mfa/disable` — Requires auth, takes password confirmation, disables MFA, clears secret
- `POST /auth/mfa/challenge` — Takes partial token + TOTP code, returns full JWT

**Modified login** (auth.py):
```python
# After password verification:
if user.mfa_enabled:
    partial_token = create_partial_token(str(user.id))  # 5 min expiry, mfa_challenge=true
    return {"partial_token": partial_token, "mfa_required": True}
else:
    token = create_full_token(str(user.id))
    return {"access_token": token}
```

**Modified `get_current_user`**: Check `payload.get("mfa_challenge")` — reject if true.

**Partial token**:
```python
def create_partial_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=5)
    return jwt.encode(
        {"sub": user_id, "exp": expire, "mfa_challenge": True},
        settings.secret_key,
        algorithm=settings.algorithm,
    )
```

**Frontend login flow**:
1. User enters email + password → calls `/auth/login`
2. If response has `access_token` → normal flow (store token, call `/me`, redirect to dashboard)
3. If response has `partial_token` + `mfa_required` → show TOTP input step
4. User enters 6-digit code → calls `/auth/mfa/challenge` with `partial_token` + `code`
5. Receives `access_token` → normal flow

**Frontend MFA setup**:
- New page `/dashboard/mfa` in sidebar
- Calls `/auth/mfa/setup` → displays QR code (via `qrcode` library or data URI)
- User scans with Google Authenticator, enters code to verify
- MFA enabled after successful verification
- "Disable MFA" button with password confirmation

**Test scenarios (10-15 backend tests)**:
1. Setup generates secret and QR URI
2. Verify with correct code enables MFA
3. Verify with incorrect code returns 400
4. Verify before setup returns 400
5. Disable with correct password works
6. Disable with wrong password returns 401
7. Login returns partial token when MFA enabled
8. Login returns full token when MFA disabled
9. Challenge with valid partial + correct code returns full JWT
10. Challenge with valid partial + wrong code returns 401
11. Challenge with expired partial token returns 401
12. Challenge with full JWT (not partial) returns 400
13. /auth/me rejects partial token (401)
14. Setup after MFA already enabled regenerates secret
15. Double disable returns 400

### Risks

- **Partial token window**: 5-minute window where a leaked partial token could be used for challenge brute force. Mitigation: rate-limit `/auth/mfa/challenge` (e.g., 5 attempts per minute per user), use short expiry.
- **Secret storage**: `mfa_secret` stored in plaintext in DB. If DB is compromised, TOTP secrets are exposed. Acceptable for this product scope; encryption can be added later.
- **Backward compatibility**: Existing tokens in localStorage (issued before MFA deploy) remain valid — users won't be forced into MFA. No data migration needed since new fields default to null/false.
- **Frontend login refactor**: Login page needs conditional rendering for MFA step. Mitigation: keep it simple — same page, conditional TOTP input shown when `mfa_required` is true.
- **pyotp library risk**: Simple, stable library (no breaking changes expected), MIT license, 1 dependency (six).

### Ready for Proposal

Yes. The exploration is complete and the approach is well-defined. The user should be informed that:
- MFA will use the partial-token two-step login pattern (Google Authenticator-compatible)
- Backend changes: new mfa.py routes, User model additions, minimal auth.py modifications
- Frontend changes: login flow split, new MFA setup page in dashboard
- ~10-15 new backend tests
- pyotp added to requirements.txt
- No new env vars needed
- Existing sessions/tokens remain valid
