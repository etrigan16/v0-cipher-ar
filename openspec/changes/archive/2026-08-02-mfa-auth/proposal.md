# Proposal: MFA / TOTP Authentication

## Intent

Add optional Google Authenticator-compatible TOTP as a second authentication factor. Currently the system has password-only login — users with MFA enabled must verify a 6-digit TOTP code after password validation before receiving a full JWT session.

## Scope

### In Scope
- User model: add `mfa_secret` (nullable) and `mfa_enabled` (bool, default false) columns
- Auth flow: login returns a 5-min partial token when MFA is enabled; `get_current_user` rejects partial tokens
- New routes: `/auth/mfa/setup`, `/auth/mfa/verify`, `/auth/mfa/disable`, `/auth/mfa/challenge`
- Frontend: conditional TOTP input step in login flow; new `/dashboard/mfa` setup page with QR code
- Tests: ~15 backend scenarios (setup, verify, challenge, reject wrong codes/expired tokens)
- Dependency: add `pyotp` to `backend/requirements.txt`

### Out of Scope
- Recovery/backup codes
- Email/SMS fallback MFA
- Biometric or WebAuthn
- Multi-tenant MFA policies
- Encryption of stored TOTP secrets (acceptable at current scope)

## Capabilities

### New Capabilities
- `mfa-auth`: TOTP-based multi-factor authentication — setup, verification, challenge, disable

### Modified Capabilities
- None (no existing spec touches auth behavior)

## Approach

Two-step login with partial tokens (Approach 1 from exploration). Login checks `user.mfa_enabled`: if true, returns a short-lived JWT with `mfa_challenge: true` claim (5 min expiry). Client presents partial token + TOTP code to `/auth/mfa/challenge` for a full JWT. Non-MFA users see no change.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/models/user.py` | Modified | Add `mfa_secret`, `mfa_enabled` columns |
| `backend/app/routes/auth.py` | Modified | Login returns partial token for MFA users; `get_current_user` rejects partial tokens |
| `backend/app/routes/mfa.py` | New | Setup, verify, disable, challenge routes |
| `backend/app/main.py` | Modified | Register mfa router |
| `backend/requirements.txt` | Modified | Add `pyotp` |
| `backend/tests/test_auth.py` | Modified | ~15 new MFA scenarios |
| `lib/api.ts` | Modified | Add `api.auth.mfa` namespace |
| `components/auth-context.tsx` | Modified | Add `mfaChallenge` state + two-step login |
| `app/login/page.tsx` | Modified | Conditional TOTP input step |
| `app/dashboard/mfa/page.tsx` | New | QR setup + verify + disable UI |
| `app/dashboard/layout.tsx` | Modified | Add MFA settings sidebar link |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Partial token leaked during 5-min window | Low | Rate-limit `/auth/mfa/challenge` (5 attempts/min per user) |
| Plaintext TOTP secrets in DB | Medium | Acceptable for current scope; encryption can be added later |
| Broken existing sessions after deploy | Low | Existing tokens remain valid; no migration needed (null defaults) |

## Rollback Plan

1. Remove `mfa_secret`/`mfa_enabled` from User model
2. Revert `auth.py` login and `get_current_user` to original
3. Delete `routes/mfa.py` and unregister from `main.py`
4. Remove `pyotp` from requirements.txt
5. Revert frontend: login page, auth-context, api.ts, remove dashboard/mfa page
6. No data loss — existing tokens and sessions are unaffected

## Dependencies

- `pyotp` (MIT license, stable, single dependency)

## Success Criteria

- [ ] All 15 backend MFA tests pass
- [ ] Non-MFA login flow unchanged (no partial token, same UX)
- [ ] MFA user sees QR code in `/dashboard/mfa`, can verify and enable
- [ ] MFA user must enter TOTP at login; wrong codes rejected
- [ ] Partial tokens rejected by all protected endpoints
- [ ] MFA enabled user can disable with correct password
