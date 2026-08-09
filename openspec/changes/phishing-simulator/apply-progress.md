# Apply Progress — phishing-simulator (PR 5: Phase 5)

- **Change**: phishing-simulator
- **Batch**: PR 5 of feature-branch-chain (`feature/phishing-simulator-p5` → previous PR branch `feature/phishing-simulator-p4` → tracker `feature/phishing-simulator`)
- **Scope**: Phase 5 (Results + PDF). NO frontend (Phase 6 is PR 6).
- **Mode**: Strict TDD (openspec/config.yaml `apply.tdd: true`)
- **Artifact store**: hybrid
- **Date**: 2026-08-09
- **Commit range**: 637e476 (PR4 HEAD) → PR5 HEAD (2 work-unit commits: 734d3b2, b80f181)

## Status — 21/28 tasks complete (Phases 1 + 2 + 3 + 4 + 5)

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

### Phase 4 (PR 4 — merged from previous batch)

| Task | Status |
|------|--------|
| 4.1 RED (threat matrix D5): `?url=https://evil` still 302 → `/l/{token}`; expired token → 410, no Event | [x] |
| 4.2 RED: open/click/landing/credential/report flows, 7-day expiry, IP/UA metadata, plaintext never stored (tracking R1–R6) | [x] |
| 4.3 `services/phishing/landing.py`: token→Target lookup, expiry rule (D2), Event recording with ip/user_agent | [x] |
| 4.4 Create `routes/tracking.py`: `/track/open/{token}.png` (1×1 PNG, no-store), `/track/click/{token}` (302 → `/l/{token}`), `GET /l/{token}` (render + notice + form), `POST /l/{token}/submit` (sha256 hash only → Event(credential), discard plaintext — D4), `POST /l/{token}/report` | [x] |
| 4.5 `main.py`: import + include tracking router | [x] |

### Phase 5 (PR 5 — this batch)

| Task | Status |
|------|--------|
| 5.1 RED: per-target results, summary zeroed (200), PDF `%PDF` magic + empty campaign (results R1–R3) | [x] |
| 5.2 `services/phishing/results.py`: per-target activity + aggregate counts/rates (open/click/credential) | [x] |
| 5.3 `services/reports/phishing_pdf.py` (PR-5 resolution of design D8): `ExportCampaignTarget` + `generate_campaign_pdf` reusing `_table_style` | [x] |
| 5.4 `routes/phishing.py`: `GET /campaigns/{id}/results`, `GET /results-summary`, `GET /campaigns/{id}/export?format=csv|pdf` | [x] |

**4/4 Phase 5 tasks complete.** Ready for next batch (PR 6: frontend).

## Work Unit Evidence (PR 5)

| Work unit | Focused test command + result | Runtime harness + result | Rollback boundary |
|-----------|-------------------------------|--------------------------|-------------------|
| 1. Results service + report generators | `pytest tests/test_phishing_results.py -q` (at commit 734d3b2) → 9 passed (unit layer only: build_target_result ×3, summarize ×2, generate_results_csv ×2, generate_campaign_pdf ×2) | N/A for the unit layer — pure functions (no I/O, no DB); the reportlab PDF path is exercised by the unit test asserting real `%PDF` bytes + extracted text tokens | Revert 734d3b2 — `results.py` + `phishing_pdf.py` are only imported by the routes added in the next commit |
| 2. Results/summary/export endpoints | `pytest tests/test_phishing_results.py -q` (at b80f181) → 25 passed (9 unit + 16 integration) | ASGITransport + in-memory SQLite (conftest `client`): real register/login → template → campaign → CSV → launch → public tracking endpoints produce Events (open pixel, click, credential submit, report) → auth'd GET `/campaigns/{id}/results` (flags+timestamps), GET `/results-summary` (rates), GET `/campaigns/{id}/export?format=csv\|pdf` (Content-Type/Disposition, `%PDF` magic, CSV columns) — real HTTP verbs, tenant-scoped | Revert b80f181 — drop the 3 routes from `routes/phishing.py` + integration classes in the test file; services/generators/tables stay (additive) |

Full suite at PR5 HEAD: `pytest -q` → **288 passed, 2 skipped** (PR4 baseline 263 + 25 new, 0 regressions).
Focused slice command (tasks.md unit 5): `pytest -k "results or summary or pdf"` → 25 passed.

## TDD Cycle Evidence (PR 5)

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 5.2 results.py (per-target + summary + CSV) | `tests/test_phishing_results.py` | Unit (pure) | ✅ 83/83 phishing subset (PR4 baseline) | ✅ Written (collection error — `app.services.phishing.results` absent) | ✅ 5 passed (build_target_result ×3, summarize ×2, generate_results_csv ×2 in unit layer) | ✅ 7 cases (no events, mixed activity, landing-only ignored; summary from real data + empty zeros; CSV rows + headers-only) | ✅ Pure functions with typed dataclasses; rate math extracted into `summarize` (single source for counts/rates) |
| 5.3 phishing_pdf.py (`generate_campaign_pdf`) | `tests/test_phishing_results.py` | Unit (pure, reportlab) | ✅ 83/83 phishing subset | ✅ Written (import error — module absent) | ✅ 2 passed (one test fixture fixed: 3 targets / 2 opened so the 66.67% rate is real) | ✅ 2 cases (PDF with data: title/summary/table tokens; empty campaign: `%PDF` + "No targets" + "0%") | ✅ Extracted `_percent` + `_yes_no` helpers; `_table_style` reused from `reports/generator.py` (D8) instead of duplicated |
| 5.1+5.4 routes (`/results`, `/results-summary`, `/export`) | `tests/test_phishing_results.py` | Integration (API) | ✅ 83/83 phishing subset | ✅ Written (endpoint tests fail vs absent routes — FastAPI 404) | ✅ 16 passed | ✅ 16 endpoint cases (results: mixed activity, no activity, unknown 404, cross-tenant 404, 401; summary: real data, empty zeros, tenant scoping, 401; export: CSV columns+content-type, PDF header, empty-campaign PDF, invalid format 400, missing format 400, cross-tenant 404, 401) | ✅ Shared `_load_results` helper (campaign vs tenant scope via optional `campaign_id`), `_result_dto`; export mirrors `asm.py` pattern (format gate → 400, `Content-Disposition`) |

### Test Summary (PR 5)
- **Total tests written**: 25 (unit 9: build_target_result 3, summarize 2, generate_results_csv 2, generate_campaign_pdf 2; integration 16)
- **Total tests passing**: 25/25 in new file; full suite 288 passed / 2 skipped (PR4 baseline 263 → +25, 0 regressions)
- **Layers used**: Unit (9), Integration (16)
- **Approval tests**: None — no refactoring of existing behavior (services + routes are net-new; `phishing.py` only gained routes)
- **Pure functions created**: `build_target_result()`, `summarize()`, `generate_results_csv()` (services/phishing/results.py); `generate_campaign_pdf()`, `_percent()`, `_yes_no()` (services/reports/phishing_pdf.py)

## Files Changed (PR 5)

| File | Action | What Was Done |
|------|--------|---------------|
| `backend/app/services/phishing/results.py` | Created | Pure aggregation: `TargetResult` (email/name/status + opened/clicked/credential/reported flags + first-event timestamps), `ResultsSummary` (total/sent/opened+rate/clicked+rate/credentials/reported), `build_target_result()`, `summarize()` (rates over `sent`=active targets, 0.0 on empty), `generate_results_csv()` (stdlib csv, headers `email,name,status,opened,clicked,credential,reported`, lowercase `true`/`false`) |
| `backend/app/services/reports/phishing_pdf.py` | Created | `ExportCampaignTarget` + `generate_campaign_pdf(campaign, targets)` — A4 reportlab PDF: dark title band, Results Summary (total/sent/opened+rate/clicked+rate/credentials/reported), per-target table (email, status, opened, clicked, credentials), empty-campaign note; reuses `_table_style` from `reports/generator.py` (design D8); pure bytes |
| `backend/app/services/phishing/__init__.py` | Modified | Re-exports `TargetResult`, `ResultsSummary`, `build_target_result`, `summarize`, `generate_results_csv` |
| `backend/app/services/reports/__init__.py` | Modified | Re-exports `ExportCampaignTarget`, `generate_campaign_pdf` |
| `backend/app/routes/phishing.py` | Modified | +3 auth'd tenant-scoped routes: `GET /campaigns/{id}/results` (per-target flags + first-event timestamps), `GET /results-summary` (tenant aggregate via `asdict(summarize(...))`), `GET /campaigns/{id}/export?format=csv|pdf` (CSV via stdlib / PDF via reportlab, `Content-Disposition: attachment`, 400 on invalid/missing format); shared `_load_results` helper (targets + `MIN(occurred_at)` per (target,type) GROUP BY, tenant-filtered) |
| `backend/tests/test_phishing_results.py` | Created | 25 tests: 9 unit (pure services/generators) + 16 integration (endpoints over ASGITransport; real tracking endpoints produce Events) |

## Deviations from Design / Launch Prompt

1. **`generate_campaign_pdf` lives in a new module `services/reports/phishing_pdf.py`, NOT `services/reports/generator.py`** (design D8 said generator.py). The PR-5 launch prompt explicitly required the new module. Design intent (reuse `_table_style`, stay pure) is preserved: it imports `_table_style` from `generator.py` (D8) and keeps the ORM-free bytes contract.
2. **Export endpoint replaces spec R3's `/campaigns/{id}/report`**: the PR-5 launch prompt requires `GET /campaigns/{id}/export?format=csv|pdf` (with CSV added, plus `Content-Disposition`/Content-Type and 400 on invalid format). Tasks 5.4's `/report` wording is superseded by this resolution; spec R3's "report returning a valid PDF" maps to `export?format=pdf`. The spec delta is left for the verify/archive phase to reconcile.
3. **Rates are percentages over `sent` (active targets), not totals** — `sent` is the launch-delivered denominator (pending targets were never sent). Empty/zero-sent tenants return 0.0 (spec R2). The launch prompt's summary field set (total/sent/opened+rate/clicked+rate/credentials/reported) is exposed exactly; spec R2's "credential %" is not a separate field (credentials are a count, matching the launch prompt).
4. **`landing` events never flip a results flag** (design D3 audits them, but the results surface is open/click/credential/report per the launch prompt). Covered explicitly by a unit test.
5. **CSV bool cells render lowercase `true`/`false`** — deterministic, stdlib-safe (no locale-dependent `str(True)`).

## Issues Found

- One RED unit test had a **fixture math error** (asserted 66.67% with 2 targets/1 opened = 50%): fixed the fixture to 3 targets/2 opened so the percent computation is genuinely exercised. Production code was correct; no implementation change needed.
- The `.atl/skill-registry*` files were already dirty before this batch (session noise, unrelated) — left uncommitted.
- pytest runtime warnings (deprecated `on_event`, unawaited coroutines) are pre-existing — not introduced by this batch.

## Workload / PR Boundary

- Mode: chained PR slice (feature-branch-chain); PR 5 targets the previous PR branch `feature/phishing-simulator-p4` (tracker: `feature/phishing-simulator`)
- Boundary: starts at 637e476 (PR4 HEAD); ends with this batch's HEAD (2 work-unit commits: 734d3b2 services/generators, b80f181 routes + integration tests)
- Estimated review budget impact: **~1007 added / 6 deleted changed lines** — dominated by the 25-test file (~452 lines) and the 204-line PDF generator. The PR-5 preflight budget was 800 lines; this slice slightly exceeds it for the same reason PR4 did (RED suite + a full reportlab generator). Reviewer-facing logic is ~450 authored lines; the rest is tests. Flagged for the orchestrator: if 800 is a hard gate, PR 5 could be re-split (e.g., results+summary vs export) — otherwise accept `size:exception` for this slice.

### Status
21/28 tasks complete (6/6 Phase 1 + 3/3 Phase 2 + 3/3 Phase 3 + 5/5 Phase 4 + 4/4 Phase 5). Ready for next batch (PR 6: frontend).
