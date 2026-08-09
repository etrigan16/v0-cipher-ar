# Apply Progress — phishing-simulator (PR 1: Phase 1)

- **Change**: phishing-simulator
- **Batch**: PR 1 of feature-branch-chain (`feature/phishing-simulator-p1` → tracker `feature/phishing-simulator`)
- **Scope**: Phase 1 (Foundation) — models, migration 005, RLS, config. NO template CRUD, campaigns, tracking, results, or frontend (Phases 2-6 are later PRs).
- **Mode**: Strict TDD (openspec/config.yaml `apply.tdd: true`; pytest 9.1.1)
- **Artifact store**: hybrid
- **Date**: 2026-08-09
- **Commit range**: 33ec2d5 → 6ff27bd (4 work-unit commits)

## Status

| Task | Status |
|------|--------|
| 1.1 RED: `tests/test_migrations.py` 005 upgrade creates 4 tables + 8 seeds; downgrade drops cleanly | [x] |
| 1.2 Create `models/{template,campaign,target,event}.py` (CoercingUuid, `ix_*_tenant_id`, UQ campaign+email, unique nullable `tracking_token`, `server_default=func.now()`) | [x] |
| 1.3 Register all 4 in `models/__init__.py` | [x] |
| 1.4 Create `alembic/versions/005_phishing.py` (down_revision `004_risk_scoring`; FKs + indexes; 8 seeds tenant_id NULL: 3 bank/3 gov/2 tech, all with `{{nombre}}`,`{{empresa}}`,`{{link}}`) | [x] |
| 1.5 `database.py` `init_db`: RLS for templates/campaigns/targets/events; templates policy `tenant_id = current OR NULL` (D9) | [x] |
| 1.6 `config.py`: add `tracking_base_url` | [x] |

**6/6 Phase 1 tasks complete.** Ready for next batch (PR 2: Template CRUD + renderer).

Also covers prompt task 6 (RED tests): model persistence tests for the 4 models
(`tests/test_phishing_models.py`), migration upgrade/downgrade test
(`tests/test_migrations.py` 005 section), and RLS policy registration tests
(assert policy SQL/metadata — Postgres runtime skipped on SQLite).

## Work Unit Evidence

| Work unit | Focused test command + result | Runtime harness + result | Rollback boundary |
|-----------|-------------------------------|--------------------------|-------------------|
| 1. Models + registration | `pytest tests/test_phishing_models.py -q` → 7 passed | ORM persistence against in-memory SQLite (create_all on registered metadata); integrity violations via real flush | Revert 33ec2d5; no other code depends on the models yet |
| 2. Migration 005 | `pytest tests/test_migrations.py -q` → 9 passed | Migration ops executed against in-memory SQLite via `Operations.context` (upgrade + downgrade, seeds, constraints) | Revert 4f4fd74; `alembic downgrade 005_phishing` drops the 4 tables — additive, no existing rows touched |
| 3. RLS registration | `pytest tests/test_phishing_models.py -q` → 11 passed | N/A — RLS runtime is PostgreSQL-only (`current_setting`); SQLite lacks RLS, so tests assert the generated policy SQL/metadata (full runtime runs in CI/staging) | Revert cc51efc; init_db falls back to the pre-existing assets/scans/findings loop behavior (approval test) |
| 4. Config | `pytest tests/test_config.py -q` → 9 passed | N/A — pure settings (pydantic-settings), no runtime boundary | Revert 6ff27bd; config gains one defaulted field, nothing else reads it yet |

Full suite after all units: `pytest -q` → **180 passed, 2 skipped** (baseline was 165 passed, 2 skipped; +15 tests, 0 regressions).

## TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 1.1 Migration 005 | `tests/test_migrations.py` | Unit (migration ops) | ✅ 165/165 | ✅ Written | ✅ Passed | ✅ 2 cases (upgrade schema+seeds, downgrade) | ✅ Loader generalized to `_load_migration_module(file_name)` w/ approval |
| 1.2 Models | `tests/test_phishing_models.py` | Unit (model persistence) | ✅ 165/165 | ✅ Written | ✅ Passed | ✅ 6 cases (tenant template, NULL-seed template, campaign draft, target defaults, dup email, token unique) | ➖ None needed |
| 1.3 Registration | `tests/test_phishing_models.py` | Unit | ✅ 165/165 | ✅ Written (via model imports) | ✅ Passed | ➖ Structural (import export only) | ➖ None needed |
| 1.4 Migration file | `tests/test_migrations.py` | Unit | ✅ 165/165 | ✅ Written | ✅ Passed | ✅ seeds loop (8 rows × 3 vars, category counts) | ➖ None needed |
| 1.5 RLS | `tests/test_phishing_models.py` | Unit (policy SQL) | ✅ 165/165 | ✅ Written | ✅ Passed | ✅ 4 cases (registration map, templates OR NULL, strict no-OR, asset approval) | ✅ Extracted `_tenant_isolation_policy` + `_TENANT_RLS_TABLES` spec |
| 1.6 Config | `tests/test_config.py` | Unit | ✅ 165/165 | ✅ Written | ✅ Passed | ✅ 2 cases (default, env override) | ➖ None needed |

### Test Summary
- **Total tests written**: 15 (migration 2, model persistence 7, RLS policy 4, config 2)
- **Total tests passing**: 180 (full backend suite) / 2 skipped (RLS, PostgreSQL-only)
- **Layers used**: Unit (15) — no integration layer needed this slice (no routes yet)
- **Approval tests** (refactoring): 1 (`test_assets_policy_sql_preserved_by_refactor`) + 004 migration tests re-run after the loader refactor
- **Pure functions created**: `_tenant_isolation_policy` (database.py)

## Files Changed

| File | Action | What Was Done |
|------|--------|---------------|
| `backend/app/models/template.py` | Created | Template model (tenant_id nullable = seed rows, category, subject, html_body) |
| `backend/app/models/campaign.py` | Created | Campaign model (template FK, status draft/active/completed/cancelled, started/completed_at) |
| `backend/app/models/target.py` | Created | Target model (UQ tenant+campaign+email, unique nullable tracking_token, pending/active) |
| `backend/app/models/event.py` | Created | Event model (campaign/target FKs, type, `metadata_` → DB column `metadata`) |
| `backend/app/models/__init__.py` | Modified | Exports the 4 new models |
| `backend/alembic/versions/005_phishing.py` | Created | 4 tables + FKs + indexes + 8 NULL-tenant seeds (3 bank/3 gov/2 tech) |
| `backend/app/database.py` | Modified | Model imports; `_TENANT_RLS_TABLES` spec + `_tenant_isolation_policy`; RLS loop covers 4 new tables (templates OR NULL) |
| `backend/app/config.py` | Modified | `tracking_base_url` (default `http://localhost:8000`, env `TRACKING_BASE_URL`) |
| `backend/.env.example` | Modified | `TRACKING_BASE_URL` documented |
| `backend/tests/test_phishing_models.py` | Created | 11 tests (model persistence + RLS policy registration) |
| `backend/tests/test_migrations.py` | Modified | 005 upgrade/downgrade tests + generic migration loader |
| `backend/tests/test_config.py` | Modified | 2 tracking_base_url tests |

## Deviations from Design

- **Event `metadata` column**: design names the column `metadata`; `metadata` is a
  reserved attribute name in SQLAlchemy's declarative API (verified:
  `InvalidRequestError`). The DB column keeps the design name `metadata`; the
  ORM attribute is exposed as `metadata_` (documented in the model + migration).
  No schema change vs design — attribute name only.
- **RLS implementation**: design says "append RLS loop in init_db". Implemented
  the same semantics via a pure `_tenant_isolation_policy(table, allow_null_tenant)`
  helper + `_TENANT_RLS_TABLES` spec so the registration is testable without
  PostgreSQL. Generated SQL for the pre-existing tables is byte-identical
  (approval-tested).

## Issues Found

- SQLite's `Inspector.get_indexes` reports `unique` as `1` (int) while Postgres
  reports `True` — migration test uses a truthy assertion to stay dialect-portable.
- `docker` is not available in this environment, so the Postgres runtime harness
  (`docker compose up db` + `alembic upgrade head`) could not run; the migration
  artifact is covered by in-memory SQLite migration tests, and RLS runtime is
  covered by the Postgres-only CI/staging path (existing skip convention).

## Workload / PR Boundary

- Mode: chained PR slice (feature-branch-chain)
- Current work unit: PR 1 — Phase 1 (models + migration + RLS + config)
- Boundary: starts at `feature/phishing-simulator-p1` (targets tracker
  `feature/phishing-simulator`); ends with config commit 6ff27bd
- Estimated review budget impact: 845 added / 12 deleted changed lines (incl.
  ~340 test lines) — above the 400-line single-PR budget by design (chained
  slice); slightly above the 800-line slice budget due to per-file CoercingUuid
  duplication following repo convention. Noted for orchestrator; trimming would
  break convention.

### Status
6/6 Phase 1 tasks complete. Ready for next batch (PR 2: templates + renderer + seeds).
