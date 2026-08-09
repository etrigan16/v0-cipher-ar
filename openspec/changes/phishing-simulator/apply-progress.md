# Apply Progress — phishing-simulator (PR 3: Phase 3)

- **Change**: phishing-simulator
- **Batch**: PR 3 of feature-branch-chain (`feature/phishing-simulator-p3` → tracker `feature/phishing-simulator`)
- **Scope**: Phase 3 (Campaign CRUD + CSV upload + launch/cancel). NO tracking, results, or frontend (Phases 4-6 later PRs).
- **Mode**: Strict TDD (openspec/config.yaml `apply.tdd: true`; pytest 9.1.1)
- **Artifact store**: hybrid
- **Date**: 2026-08-09
- **Commit range**: c479e09 (PR2 HEAD) → PR3 HEAD (2 work-unit commits)

## Status — 12/28 tasks complete (Phases 1 + 2 + 3)

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

### Phase 3 (PR 3 — this batch)

| Task | Status |
|------|--------|
| 3.1 RED: campaign CRUD, CSV valid/invalid/dedupe, launch uniqueness + non-draft 409, cancel rules (campaigns R1–R6) | [x] |
| 3.2 `services/phishing/tokens.py`: `secrets.token_urlsafe(16)` generator (D1) | [x] |
| 3.3 `routes/phishing.py`: campaigns CRUD; target CSV upload (stdlib csv, validate in memory, one bulk insert, 422 + zero persisted — D6); `POST /campaigns/{id}/launch` (draft + ≥1 target, active + started_at, unique tokens + links); `POST /campaigns/{id}/cancel` (draft|active → cancelled + completed_at) | [x] |

**3/3 Phase 3 tasks complete.** Ready for next batch (PR 4: tracking + landing + hashing).

## Work Unit Evidence (PR 3)

| Work unit | Focused test command + result | Runtime harness + result | Rollback boundary |
|-----------|-------------------------------|--------------------------|-------------------|
| 1. Token generator | `pytest tests/test_phishing_tokens.py -q` → 3 passed | N/A — pure function (no I/O); deterministic same-input→same-output | Revert commit `feat(phishing): add unique tracking token generator`; nothing else imports it until the routes commit |
| 2. Campaign CRUD + CSV + launch/cancel | `pytest tests/test_phishing_campaigns.py -q` → 34 passed | ASGITransport + in-memory SQLite (conftest `client`); real register/login via `/auth`, multipart CSV upload, real HTTP verbs | Revert commit `feat(phishing): add campaign CRUD, CSV upload and launch/cancel endpoints`; `campaigns`/`targets` tables are additive — dropping routes restores the template-only stub |

Full suite at PR3 HEAD: `pytest -q` → **237 passed, 2 skipped** (PR2 baseline 200 + 37 new, 0 regressions).
Focused slice command (tasks.md unit 3): `pytest -k "campaign or target or csv or launch"` → 44 passed.

## TDD Cycle Evidence (PR 3)

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 3.2 Token generator | `tests/test_phishing_tokens.py` | Unit (pure) | ✅ 200/200 | ✅ Written (import fails — module absent) | ✅ 3 passed | ✅ 3 cases (charset, length=22, 100-gen uniqueness) | ➖ None needed (minimal by design D1) |
| 3.1+3.3 Campaign CRUD + CSV + launch/cancel | `tests/test_phishing_campaigns.py` | Integration (API) | ✅ 200/200 | ✅ Written (31 failed vs absent routes; 3 false-GREEN 404 tests flipped to real logic) | ✅ 34 passed | ✅ 34 cases (auth, create+seed template+404×2+422, list scoping+counts, detail+404×2, update+409+422+404, delete+409+404, upload valid+auth+cross-tenant+invalid email+missing email+dupe file+dupe existing+empty, launch tokens+no-targets+non-draft+404, cancel active+draft+completed+404) | ✅ Extracted `_get_owned_campaign`/`_resolve_owned_template`/`_target_count`/`_parse_targets_csv` helpers (asm.py/PR2 pattern); correlated scalar-subquery for target counts keeps the list query PostgreSQL-safe |

### Test Summary (PR 3)
- **Total tests written**: 37 (tokens 3, campaigns 34)
- **Total tests passing**: 37/37 in new files; full suite 237 passed / 2 skipped
- **Layers used**: Unit (3), Integration (34)
- **Approval tests**: None — no refactoring of existing behavior (template routes untouched, campaigns are net-new)
- **Pure functions created**: `generate_tracking_token()` (services/phishing/tokens.py), `_parse_targets_csv()` (routes/phishing.py)

## Files Changed (PR 3)

| File | Action | What Was Done |
|------|--------|---------------|
| `backend/app/services/phishing/tokens.py` | Created | `generate_tracking_token()` — `secrets.token_urlsafe(16)` (D1), 128-bit URL-safe tokens |
| `backend/app/services/phishing/__init__.py` | Modified | Package export now includes `generate_tracking_token` |
| `backend/app/routes/phishing.py` | Modified | Campaign CRUD (`POST/GET /campaigns`, `GET/PUT/DELETE /campaigns/{id}`), `POST /campaigns/{id}/targets/upload` (multipart CSV, validate-in-memory, bulk insert, 422 + zero persisted), `GET /campaigns/{id}/targets`, `POST /campaigns/{id}/launch` (draft + ≥1 target → unique tokens, active + started_at, links), `POST /campaigns/{id}/cancel` (draft|active → cancelled + completed_at). All `get_current_user` + tenant-scoped; cross-tenant/unknown → 404 |
| `backend/tests/test_phishing_tokens.py` | Created | 3 token unit tests (D1/R4) |
| `backend/tests/test_phishing_campaigns.py` | Created | 34 endpoint tests (R1–R6) |

## Deviations from Design

1. **Upload path is nested** (`POST /phishing/campaigns/{id}/targets/upload`, launch prompt) vs spec R2 / design data flow literal URL `POST /phishing/targets/upload`. Nested is behavior-equivalent (campaign derived from path, CSV columns unchanged `email,name`) and consistent with the launch prompt's `GET /phishing/campaigns/{id}/targets` (which appears only in the prompt). The `GET /campaigns/{id}/targets` listing endpoint was also added per the prompt. Flagged for the reviewer.
2. **Launch requires ≥1 target** (launch prompt + spec R4 "with targets") — the design's "bounded 100–2000" target-count range was NOT implemented as a validation (spec has no count bounds; a 100-minimum would contradict the prompt's "at least 1 target"). Upper bound can be added in 3 lines if the reviewer wants it.
3. **Cancel allows draft|active** (spec R5 "Only draft or active campaigns MAY be cancelled" + tasks 3.3 "draft|active → cancelled") — the launch prompt's "409 if not active" was treated as shorthand for the completed/cancelled case. Completed → 409 (tested).
4. **Uploads rejected on non-draft campaigns (409)** — not in spec, but defensible: tokens are assigned at launch, so adding targets afterwards is incoherent. Small, documented extension.
5. **PUT accepts `status` for domain validation only** — spec R1 requires an out-of-domain status update → 422 with status unchanged; transitions themselves stay owned by launch/cancel (a direct PUT cannot bypass token generation). A valid in-domain `status` in the body is validated but not applied.
6. **Target `status` → `active` at launch** — design model domain is `pending|active`; launch flips each target to `active` alongside token assignment (coherent with the campaign becoming active).

## Issues Found

- 3 tests in the RED run passed trivially (`test_create_campaign_unknown_template_404`, `test_create_campaign_cross_tenant_template_404`, `test_get_campaign_unknown_404`) because the routes did not exist (FastAPI 404). These are false GREENs during RED; after implementation they pass for the right reason (tenant/template filter → 404). All other 31 failed during RED as expected.
- Launch response initially omitted `target.status`; the test caught it (KeyError) — added `status` to the per-target launch payload.
- pytest runtime warnings (deprecated `on_event`, unawaited coroutines) are pre-existing — not introduced by this batch.

## Workload / PR Boundary

- Mode: chained PR slice (feature-branch-chain); PR 3 targets the previous PR branch `feature/phishing-simulator-p2` (tracker: `feature/phishing-simulator`)
- Boundary: starts at c479e09 (PR2 HEAD); ends with this batch's HEAD
- Estimated review budget impact: **~1090 added / 21 deleted changed lines (code + tests)** — the campaign slice is inherently one deliverable (CRUD + CSV + launch/cancel share the same tables/routes) and exceeds the 800-line slice budget; the diff is dominated by the 548-line integration test file (34 tests covering spec R1–R6 + launch-prompt cases). Flagged for the reviewer — the test file is the natural split point if a smaller slice is preferred.

### Status
12/28 tasks complete (6/6 Phase 1 + 3/3 Phase 2 + 3/3 Phase 3). Ready for next batch (PR 4: tracking router + landing + hashing).
