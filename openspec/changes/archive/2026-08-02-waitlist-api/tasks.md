# Tasks: Waitlist API

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~420 |
| 400-line budget risk | Medium |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 (Backend) → PR 2 (Frontend) |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: Medium

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Backend: model, route, config, BE tests | PR 1 | `pytest backend/tests/test_waitlist.py -v` | `uvicorn backend.app.main:app` + curl `POST /api/v1/waitlist` | Revert `main.py` router registration + delete `models/waitlist.py`, `routes/waitlist.py` |
| 2 | Frontend: component, API layer, FE tests, page wiring | PR 2 | `npx vitest run` | Load landing page, submit in WaitlistSection | Revert `page.tsx` + delete `components/waitlist.tsx` + revert `lib/api.ts` |

## Phase 1: Backend Infrastructure

- [x] 1.1 Create `backend/app/models/waitlist.py` — WaitlistEntry model (id, email unique, company optional, source, created_at)
- [x] 1.2 Update `backend/app/config.py` — add `resend_api_key: str` to Settings
- [x] 1.3 Update `backend/app/models/__init__.py` — export WaitlistEntry
- [x] 1.4 Update `backend/app/database.py` — import WaitlistEntry in init_db()
- [x] 1.5 Update `backend/.env.example` — add `RESEND_API_KEY=` line

## Phase 2: Backend Route

- [x] 2.1 Create `backend/app/routes/waitlist.py` — POST /api/v1/waitlist with Pydantic validation, in-memory cooldown dict, async SQLAlchemy insert, fire-and-forget Resend email via httpx
- [x] 2.2 Update `backend/app/main.py` — register waitlist.router

## Phase 3: Frontend

- [x] 3.1 Modify `lib/api.ts` — add `api.waitlist.submit(email, company?)`
- [x] 3.2 Create `components/waitlist.tsx` — "use client" form with email/company inputs, idle/loading/success/error states, client-side validation
- [x] 3.3 Modify `app/page.tsx` — import and render `<WaitlistSection />` between PricingSection and ContactSection

## Phase 4: Backend Tests

- [x] 4.1 Create `backend/tests/test_waitlist.py` — cover all 10 scenarios: 201 valid / with-company, 422 missing / invalid-email, 409 duplicate, 429 cooldown-active, 201 cooldown-expired, Resend sends on success, 201 + warning on Resend failure, 500 DB failure

## Phase 5: Frontend Tests

- [x] 5.1 Modify `lib/api.test.ts` — add tests for `api.waitlist.submit` POST body and URL correctness
- [x] 5.2 Write vitest component test for WaitlistSection: renders inputs and submit, shows success on 201, inline error on invalid email, error state on API failure
