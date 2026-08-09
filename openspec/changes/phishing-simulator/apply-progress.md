# Apply Progress — phishing-simulator (PR 4: Phase 4)

- **Change**: phishing-simulator
- **Batch**: PR 4 of feature-branch-chain (`feature/phishing-simulator-p4` → tracker `feature/phishing-simulator`)
- **Scope**: Phase 4 (Public tracking + landing + hashing). NO results, PDF, or frontend (Phases 5-6 later PRs).
- **Mode**: Strict TDD (openspec/config.yaml `apply.tdd: true`; pytest 9.1.1)
- **Artifact store**: hybrid
- **Date**: 2026-08-09
- **Commit range**: ae31822 (PR3 HEAD) → PR4 HEAD (2 work-unit commits: 48eaabc, fa1e122)

## Status — 17/28 tasks complete (Phases 1 + 2 + 3 + 4)

### Phase 1 (PR 1 — merged from previous batch)

| Task | Status |
|------|--------|
| 1.1 RED: `tests/test_migrations.py` 005 upgrade creates 4 tables + 8 seeds; downgrade drops cleanly | [x] |
| 1.2 Create `models/{template,campaign,target,event}.py` (CoercingUuid, `ix_*_tenant_id`, UQ campaign+email, unique nullable `tracking_token`, `server_default=func.now()`) | [x] |
| 1.3 Register all 4 in `models/__init__.py` | [x] |
| 1.4 Create `alembic/versions/005_phishing.py` (down_revision `004_risk_scoring`; FKs + indexes; 8 seeds tenant_id NULL: 3 bank/3 gov/2 tech, all with `{{nombre}}`,`{{empresa}}`,`{{link}}`) | [x] |
| 1.5 `database.py` `init_db`: RLS for templates/campaigns/targets/events; templates policy `tenant_id = current OR NULL` (D9) | [x] |
| 1.6 `config.py`: add `tracking_base_url` | [x] |

### Phase 2 (PR 2 — merged from previous batch)

| Task | Status |
|------|--------|
| 2.1 RED: template CRUD, cross-tenant 404, seed visibility, render escape/missing-var (templates R1–R4) | [x] |
| 2.2 `services/phishing/render.py`: 3-key `str.replace` + `html.escape` on target values, missing → empty (D7) | [x] |
| 2.3 `routes/phishing.py`: `GET/POST /templates`, `GET/PUT/DELETE /templates/{id}` with `get_current_user`; unknown/cross-tenant → 404 | [x] |

### Phase 3 (PR 3 — merged from previous batch)

| Task | Status |
|------|--------|
| 3.1 RED: campaign CRUD, CSV valid/invalid/dedupe, launch uniqueness + non-draft 409, cancel rules (campaigns R1–R6) | [x] |
| 3.2 `services/phishing/tokens.py`: `secrets.token_urlsafe(16)` generator (D1) | [x] |
| 3.3 `routes/phishing.py`: campaigns CRUD; target CSV upload (stdlib csv, validate in memory, one bulk insert, 422 + zero persisted — D6); `POST /campaigns/{id}/launch` (draft + ≥1 target, active + started_at, unique tokens + links); `POST /campaigns/{id}/cancel` (draft|active → cancelled + completed_at) | [x] |

### Phase 4 (PR 4 — this batch)

| Task | Status |
|------|--------|
| 4.1 RED (threat matrix D5): `?url=https://evil` still 302 → `/l/{token}`; expired token → 410, no Event | [x] |
| 4.2 RED: open/click/landing/credential/report flows, 7-day expiry, IP/UA metadata, plaintext never stored (tracking R1–R6) | [x] |
| 4.3 `services/phishing/landing.py`: token→Target lookup, expiry rule (D2), Event recording with ip/user_agent | [x] |
| 4.4 Create `routes/tracking.py`: `/track/open/{token}.png` (1×1 PNG, no-store), `/track/click/{token}` (302 → `/l/{token}`), `GET /l/{token}` (render + notice + form), `POST /l/{token}/submit` (sha256 hash only → Event(credential), discard plaintext — D4), `POST /l/{token}/report` | [x] |
| 4.5 `main.py`: import + include tracking router | [x] |

**5/5 Phase 4 tasks complete.** Ready for next batch (PR 5: results + PDF).

## Work Unit Evidence (PR 4)

| Work unit | Focused test command + result | Runtime harness + result | Rollback boundary |
|-----------|-------------------------------|--------------------------|-------------------|
| 1. Expiry rule + event recorder | `pytest tests/test_phishing_tracking.py -q` (at commit 48eaabc) → 6 passed (expiry unit tests) | N/A — pure function (`is_tracking_expired`) + DB insert helper covered by endpoint tests | Revert 48eaabc; `events`/`landing` services are only imported by the tracking router (added next commit) |
| 2. Tracking routes + main | `pytest tests/test_phishing_tracking.py -q` → 26 passed (6 unit + 20 endpoint) | ASGITransport + in-memory SQLite (conftest `client`): real register/login → template → campaign → CSV → launch → then PUBLIC token flows (pixel bytes, 302 Location, rendered HTML, form submit, report) with real HTTP verbs; OpenAPI schema shows all 5 routes registered | Revert fa1e122; remove `app.include_router(tracking.router)` + `routes/tracking.py` — tables and services stay (additive) |

Full suite at PR4 HEAD: `pytest -q` → **263 passed, 2 skipped** (PR3 baseline 237 + 26 new, 0 regressions).
Focused slice command (tasks.md unit 4): `pytest -k "tracking or landing or credential or expiry"` → 26 passed.

## TDD Cycle Evidence (PR 4)

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 4.3 Expiry rule (D2) | `tests/test_phishing_tracking.py` | Unit (pure) | ✅ 72/72 phishing subset (PR3 baseline) | ✅ Written (collection error — `landing` module absent) | ✅ 6 passed | ✅ 6 cases (active, completed 6d, completed 8d, cancelled, draft, naive SQLite datetime) | ➖ None needed (minimal by D2) |
| 4.1+4.2+4.4+4.5 Public tracking endpoints | `tests/test_phishing_tracking.py` | Integration (API) | ✅ 72/72 phishing subset | ✅ Written (15 failed vs absent routes; 5 false-GREEN 404 tests flip to real logic post-impl) | ✅ 26 passed | ✅ 20 endpoint cases (open pixel + unknown/expired, click 302 + D5 guard ×2 + unknown/expired, landing render/escape + unknown/expired, credential hash + plaintext-never-stored + unknown/expired, report + unknown/expired, 6-day window) | ✅ Extracted `_resolve_or_404` (404 vs 410 mapping), `_request_metadata` (R5 ip/UA), `_click_tracking_url`, PNG byte builder; `db.get(Template, …)` over explicit select; typed return |

### Test Summary (PR 4)
- **Total tests written**: 26 (expiry unit 6, endpoint integration 20)
- **Total tests passing**: 26/26 in new file; full suite 263 passed / 2 skipped
- **Layers used**: Unit (6), Integration (20)
- **Approval tests**: None — no refactoring of existing behavior (services + routes are net-new)
- **Pure functions created**: `is_tracking_expired()`, `sha256_hex()`, `credential_hash()`, `resolve_tracking_target()` (services/phishing/landing.py); `record_event()` (services/phishing/events.py); `_png_chunk()`/`_click_tracking_url()`/`_request_metadata()` (routes/tracking.py)

## Files Changed (PR 4)

| File | Action | What Was Done |
|------|--------|---------------|
| `backend/app/services/phishing/landing.py` | Created | `is_tracking_expired()` (D2 campaign-state expiry: active → valid; completed → 7d past `completed_at`; else expired; naive-datetime-safe), `resolve_tracking_target()` (token → (Target, Campaign, expired) | None), `sha256_hex()` + `credential_hash()` (D4 one-way hashing) |
| `backend/app/services/phishing/events.py` | Created | `record_event(db, *, tenant_id, campaign_id, target_id, type, metadata)` → JSON-encoded Event row (D3), commits before response |
| `backend/app/services/phishing/__init__.py` | Modified | Exports `record_event`, `resolve_tracking_target`, `is_tracking_expired`, `credential_hash`, `sha256_hex` |
| `backend/app/routes/tracking.py` | Created | Public router (no prefix, no auth): `GET /track/open/{token}.png` (1×1 transparent PNG, no-store, records open), `GET /track/click/{token}?url=` (records click, ALWAYS 302 → `/l/{token}` — D5, `?url=` metadata-only), `GET /l/{token}` (renders template with `{{nombre}}`/`{{link}}`, notice + credential form, records landing), `POST /l/{token}/submit` (Form username/password → SHA-256 hashes only → records credential → success page), `POST /l/{token}/report` (records report → confirmation). Unknown → 404, expired → 410, no Event either way |
| `backend/app/main.py` | Modified | `from app.routes import … tracking` + `app.include_router(tracking.router)` |
| `backend/tests/test_phishing_tracking.py` | Created | 26 tests: 6 expiry unit (D2/R5) + 20 endpoint integration (R1–R6, D4/D5) |

## Deviations from Design / Launch Prompt

1. **Click redirect follows design D5, NOT the launch prompt's "redirect to `?url=` when http/https"**. Spec R2 ("redirecting the visitor to the target's landing link"), design D5 ("always 302 → `/l/{token}`; `?url=` in metadata only") and tasks 4.1 RED (`?url=https://evil` still 302 → `/l/{token}`) all agree the redirect target is always the landing page — following `?url=` (even http/https-only) is precisely the open-redirect behavior D5 rejects. `?url=` is recorded in click Event metadata. The D5 threat-matrix RED tests cover both `https://evil…` and `javascript:…` values.
2. **Expiry uses campaign state (design D2/spec R5), NOT `Target.created_at + 7 days` as the launch prompt stated.** The design's rule is "valid while `active`; `completed` → 7d past `completed_at`; else 410" and spec R5's scenario ("campaign completed 8 days ago → 410") is only satisfiable with `completed_at`-based expiry — a `created_at`-based rule would keep a long-completed campaign's links live. The exact check is `is_tracking_expired()` in `services/phishing/landing.py`.
3. **Expired → 410 (spec R2/R3/R5 explicit), unknown → 404** — the launch prompt said "expired 404"; spec requires 410 for expired tokens.
4. **Credential metadata is a superset of both authority sources**: `username_sha256`, `password_sha256` (launch prompt) AND the D4 combined `hash = sha256(f"{username}:{password}")` (design D4). No plaintext anywhere.
5. **`{{link}}` bait**: no per-campaign bait field exists in the model, so the landing page itself is the bait URL carried by the click tracking URL (D5 metadata-only semantics). `{{empresa}}` has no source field → renders empty per D7 (missing key → empty).
6. **Submit returns 200 success page** (design interface says 200; launch prompt allowed "success page or 204").
7. **Landing page/notice/form copy in Spanish** — matches the existing Spanish seed templates (product is Argentine SMB); neutral register, no slang.

## Issues Found

- 5 RED endpoint tests passed trivially (routes absent → FastAPI 404): the five `*_unknown_token_404_no_event` tests. False GREENs during RED; after implementation they pass for the right reason (token lookup → 404). The other 15 failed during RED as expected.
- A leftover drafting placeholder in `landing_page` (dead `db.get` expression + in-function import) was removed during REFACTOR before commit — no test impact.
- pytest runtime warnings (deprecated `on_event`, unawaited coroutines) are pre-existing — not introduced by this batch.

## Workload / PR Boundary

- Mode: chained PR slice (feature-branch-chain); PR 4 targets the previous PR branch `feature/phishing-simulator-p3` (tracker: `feature/phishing-simulator`)
- Boundary: starts at ae31822 (PR3 HEAD); ends with this batch's HEAD (2 work-unit commits)
- Estimated review budget impact: **~870 added / 8 deleted changed lines (code + tests)** — dominated by the 26-test file (~460 lines) and the 269-line router. Within the 800-line slice budget if the test file is counted; flagged for the reviewer — the router + services are ~380 authored lines, the rest is tests.

### Status
17/28 tasks complete (6/6 Phase 1 + 3/3 Phase 2 + 3/3 Phase 3 + 5/5 Phase 4). Ready for next batch (PR 5: results + PDF).
