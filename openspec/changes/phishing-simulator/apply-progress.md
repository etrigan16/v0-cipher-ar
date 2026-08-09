# Apply Progress — phishing-simulator (PR 2: Phase 2)

- **Change**: phishing-simulator
- **Batch**: PR 2 of feature-branch-chain (`feature/phishing-simulator-p2` → tracker `feature/phishing-simulator`)
- **Scope**: Phase 2 (Template CRUD + renderer). NO campaigns, tracking, results, or frontend (Phases 3-6 later PRs).
- **Mode**: Strict TDD (openspec/config.yaml `apply.tdd: true`; pytest 9.1.1)
- **Artifact store**: hybrid
- **Date**: 2026-08-09
- **Commit range**: 1d13f6f (PR1 HEAD) → 61fba37 (PR2 HEAD, 2 work-unit commits)

## Status — 9/28 tasks complete (Phase 1 + Phase 2)

### Phase 1 (PR 1 — merged from previous batch)

| Task | Status |
|------|--------|
| 1.1 RED: `tests/test_migrations.py` 005 upgrade creates 4 tables + 8 seeds; downgrade drops cleanly | [x] |
| 1.2 Create `models/{template,campaign,target,event}.py` (CoercingUuid, `ix_*_tenant_id`, UQ campaign+email, unique nullable `tracking_token`, `server_default=func.now()`) | [x] |
| 1.3 Register all 4 in `models/__init__.py` | [x] |
| 1.4 Create `alembic/versions/005_phishing.py` (down_revision `004_risk_scoring`; FKs + indexes; 8 seeds tenant_id NULL: 3 bank/3 gov/2 tech, all with `{{nombre}}`,`{{empresa}}`,`{{link}}`) | [x] |
| 1.5 `database.py` `init_db`: RLS for templates/campaigns/targets/events; templates policy `tenant_id = current OR NULL` (D9) | [x] |
| 1.6 `config.py`: add `tracking_base_url` | [x] |

### Phase 2 (PR 2 — this batch)

| Task | Status |
|------|--------|
| 2.1 RED: template CRUD, cross-tenant 404, seed visibility, render escape/missing-var (templates R1–R4) | [x] |
| 2.2 `services/phishing/render.py`: 3-key `str.replace` + `html.escape` on target values, missing → empty (D7) | [x] |
| 2.3 `routes/phishing.py`: `GET/POST /templates`, `GET/PUT/DELETE /templates/{id}` with `get_current_user`; unknown/cross-tenant → 404 | [x] |

**3/3 Phase 2 tasks complete.** Ready for next batch (PR 3: Campaign CRUD + CSV + launch/cancel).

## Work Unit Evidence (PR 2)

| Work unit | Focused test command + result | Runtime harness + result | Rollback boundary |
|-----------|-------------------------------|--------------------------|-------------------|
| 1. Renderer service | `pytest tests/test_phishing_render.py -q` → 7 passed | N/A — pure function (no I/O); deterministic same-input→same-output | Revert commit `feat(phishing): add template variable substitution renderer`; routes never import render yet, nothing else depends on it |
| 2. Template CRUD | `pytest tests/test_phishing_templates.py -q` → 13 passed | ASGITransport + in-memory SQLite (conftest `client`); real register/login via `/auth`, real HTTP verbs against the app | Revert commit `feat(phishing): add tenant-scoped template CRUD endpoints`; table `templates` is additive — dropping routes restores the stub behavior |

Full suite at PR2 HEAD: `pytest -q` → **200 passed, 2 skipped** (PR1 baseline 180 + 20 new, 0 regressions).
Focused slice command (tasks.md unit 2): `pytest -k "template or render"` → 26 passed.

## TDD Cycle Evidence (PR 2)

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 2.2 Renderer | `tests/test_phishing_render.py` | Unit (pure) | ✅ 180/180 | ✅ Written (import fails — module absent) | ✅ 7 passed | ✅ 7 cases (all-vars, extra key, missing, escape, attr-escape, repeated, empty context) | ➖ None needed (minimal by design D7) |
| 2.3 Template CRUD | `tests/test_phishing_templates.py` | Integration (API) | ✅ 180/180 | ✅ Written (404s against stub) | ✅ 13 passed | ✅ 13 cases (auth 401, create+list, 422×2, seeds, isolation, detail, unknown 404, cross-tenant 404×3, update, delete) | ✅ Extracted `_coerce_uuid`/`_template_dto` helpers (asm.py pattern); split single test file into render + templates files for work-unit commits |

### Test Summary (PR 2)
- **Total tests written**: 20 (renderer 7, templates CRUD 13)
- **Total tests passing**: 20/20 in new files; full suite 200 passed / 2 skipped
- **Layers used**: Unit (7), Integration (13)
- **Approval tests**: None — no refactoring of existing behavior (routes were a placeholder stub, replaced)
- **Pure functions created**: `render()` (services/phishing/render.py)

## Files Changed (PR 2)

| File | Action | What Was Done |
|------|--------|---------------|
| `backend/app/services/phishing/render.py` | Created | `render(template_html, context)` — fixed 3-key `str.replace` + `html.escape` on values; missing standard var → empty; extra context keys substituted (D7) |
| `backend/app/services/phishing/__init__.py` | Created | Package export (`render`); docs note later phases add tokens/landing/results |
| `backend/app/routes/phishing.py` | Modified | Stub replaced: GET/POST `/templates`, GET/PUT/DELETE `/templates/{id}`, `get_current_user`, tenant-scoped; seeds readable (list+detail), PUT/DELETE own-rows-only 404 |
| `backend/tests/test_phishing_render.py` | Created | 7 renderer unit tests (R4) |
| `backend/tests/test_phishing_templates.py` | Created | 13 CRUD endpoint tests (R1–R3) |

## Deviations from Design

1. **Renderer path**: design.md File Changes lists `backend/app/services/phishing/{render,...}.py` and tasks.md 2.2 says `services/phishing/render.py` — followed the design/tasks path (`services/phishing/render.py`), not the launch prompt's shorthand `services/renderer.py`. Keeps the phishing service package coherent for PRs 3-5 (tokens/landing/results land in the same package).
2. **Seed write-protection** (design-specified behavior, made explicit): GET list+detail include NULL-tenant seeds (`OR tenant_id IS NULL`, D9); PUT/DELETE scope strictly to `tenant_id == user.tenant_id`, so seeds and cross-tenant ids both 404 (spec R2 "no data leak" + seeds are global). This is the only safe read/write split for shared seed rows.
3. **401 vs 403**: launch prompt asked for "401" auth tests. The repo convention (`test_auth.py`) yields 401 for a malformed-but-present Bearer token; a missing header yields 403 (HTTPBearer auto_error). Tests assert the 401 path with an invalid token, matching repo convention.
4. **Renderer escape**: launch prompt said "no HTML escaping issues — templates are trusted tenant HTML"; spec R4 + design D7 explicitly require `html.escape` on target-supplied values (scenario: `<script>` must be escaped). Implemented escaping per spec/design — template body itself is trusted, substituted values are escaped.

## Issues Found

- `from tests.conftest import Session` imports a *second* module instance of conftest (fresh engine, empty tables) → seed-insert test failed with "no such table". Fixed with `from conftest import Session` (the same module pytest loaded; convention used by `test_llm_enrich.py`).
- pytest runtime warnings (deprecated `on_event`, unawaited coroutines in waitlist/llm mocks) are pre-existing — not introduced by this batch.

## Workload / PR Boundary

- Mode: chained PR slice (feature-branch-chain); PR 2 targets the previous PR branch `feature/phishing-simulator-p1` (tracker: `feature/phishing-simulator`)
- Boundary: starts at 1d13f6f (PR1 HEAD); ends with 61fba37 (this batch)
- Estimated review budget impact: ~440 added / 22 deleted changed lines (code + tests) — within the 800-line slice budget

### Status
9/28 tasks complete (6/6 Phase 1 + 3/3 Phase 2). Ready for next batch (PR 3: Campaign/Target CRUD + CSV + launch/cancel).
