# Tasks: MFA / TOTP Authentication

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 450–650 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 (Backend foundation) → PR 2 (Backend routes + login) → PR 3 (Frontend + tests) |
| Delivery strategy | ask-on-risk |
| Chain strategy | stacked-to-main |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Backend model, rate limiter, partial token utils | PR 1 | `pytest tests/test_mfa.py::TestRateLimiter -x` | `pytest tests/test_mfa.py::TestRateLimiter -x` | Revert model + rate_limiter.py + tokens.py |
| 2 | MFA routes + login modification | PR 2 | `pytest tests/test_mfa.py -x` | `pytest tests/ -x` (38 pass) | Revert routes/mfa.py + auth.py + main.py |
| 3 | Frontend: api.ts, auth-context, login TOTP, dashboard/mfa | PR 3 | `pytest tests/test_mfa.py -x` | `pytest tests/ -x` (38 pass) | Revert all frontend changes |

## Phase 1: Foundation

- [x] 1.1 Add `pyotp` to `backend/requirements.txt`
- [x] 1.2 Add `mfa_secret` (nullable String) and `mfa_enabled` (Boolean, default False) to User model in `backend/app/models/user.py`
- [x] 1.3 Create `backend/app/utils/rate_limiter.py` with `InMemoryRateLimiter` (dict[str, list[float]], 5 attempts/60s window, `check()` + `record()`)
- [x] 1.4 Add `create_partial_token()` and `validate_partial_token()` to `backend/app/utils/tokens.py` (5 min, `mfa_challenge: true` claim)

## Phase 2: Backend Routes

- [x] 2.1 Create `backend/app/routes/mfa.py` with `POST /setup` (generate secret + provisioning_uri), `POST /verify` (confirm TOTP, enable MFA), `POST /disable` (password-confirmed)
- [x] 2.2 Implement `POST /auth/mfa/challenge` in mfa.py: validate partial token, check rate limit, verify TOTP, return full 1440-min JWT
- [x] 2.3 Modify login in `auth.py`: if `user.mfa_enabled` → return partial token (`partial_token`, `mfa_required: true`); else → existing full JWT
- [x] 2.4 Update `get_current_user` in `auth.py` to reject tokens carrying `mfa_challenge: true` claim with 401
- [x] 2.5 Register `mfa.router` in `backend/app/main.py`

## Phase 3: Frontend

- [x] 3.1 Add `api.auth.mfa.setup()`, `api.auth.mfa.verify()`, `api.auth.mfa.disable()`, `api.auth.mfa.challenge()` to `lib/api.ts`
- [x] 3.2 Add `mfaChallenge` state (`null | {partialToken, email}`) and two-step login flow to `components/auth-context.tsx`
- [x] 3.3 Modify `app/login/page.tsx`: show TOTP input when `mfaChallenge` is set, disable email/password fields, wire challenge to auth-context
- [x] 3.4 Create `app/dashboard/mfa/page.tsx`: display QR code from setup, TOTP input for verify, "Disable MFA" with password confirmation
- [x] 3.5 Add MFA settings link to `app/dashboard/layout.tsx`

## Phase 4: Backend Tests

- [x] 4.1 Write unit test for `InMemoryRateLimiter`: limit hit, window expiry, reset
- [x] 4.2 Write integration tests for setup → verify → enable flow (R2, R3)
- [x] 4.3 Write integration tests for challenge: valid TOTP, invalid TOTP, expired partial token, full token rejected (R5)
- [x] 4.4 Write integration tests for login: MFA enabled returns partial token, MFA disabled returns full token, backward compat (R6, R10)
- [x] 4.5 Write integration tests for disable: correct/incorrect password, already disabled (R4)
- [x] 4.6 Write integration tests for rate limiting: 6th attempt returns 429, window expiry accepts again (R9)
- [x] 4.7 Write integration test for `get_current_user` rejecting partial tokens at protected endpoints

## Phase 5: Frontend Tests

- [ ] 5.1 Write test for login page: conditional TOTP render, challenge success stores full JWT, challenge failure shows error (R8)
- [ ] 5.2 Write test for `/dashboard/mfa` page: QR display, verify success, disable with password confirmation (R7)
