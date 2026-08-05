# Apply Progress: attack-surface-core — PR 1 + PR 2 + PR 3

**Status**: Phase 1 + Phase 2 + Phase 3 complete (18/18 tasks). Phase 4 deferred.
**Mode**: Standard (tests written alongside each work unit; no strict TDD gate).
**Delivery strategy**: chained (feature-branch-chain) — 4 PRs. PR 1, PR 2, PR 3 done.
**PR 1 branch**: `feature/attack-surface-core-p1` (targeted tracker `feature/attack-surface-core`).
**PR 2 branch**: `feature/attack-surface-core-p2` (base = p1 branch).
**PR 3 branch**: `feature/attack-surface-core-p3` (base = p2 branch).

---

## PR 1 — Data Foundation (Phase 1) [complete]

### Work Unit Evidence

| Evidence | Required value |
|---|---|
| Focused test command | `cd backend && python -m pytest tests/test_asm.py -q` → `6 passed` (upsert no-dup, model persistence, tenant isolation, scan lifecycle, finding linkage). `-k upsert` green. |
| Runtime harness | `SECRET_KEY=test RESEND_API_KEY=re_test_key python -m alembic upgrade head --sql` → valid SQL (3 tables + indexes + unique constraint). Full `pytest` → `36 passed, 2 skipped`. No Postgres locally; RLS verified offline. |
| Rollback boundary | Drop `assets`/`scans`/`findings` (`alembic downgrade 002`) + revert model/RLS/req changes. Additive. |

### Completed Tasks (Phase 1)

- [x] 1.1 `backend/app/models/asset.py` — `Asset` + `UniqueConstraint(tenant_id, domain, subdomain)`
- [x] 1.2 `Scan` (`scan.py`) + `Finding` (`finding.py`) models
- [x] 1.3 Registered models in `models/__init__.py`
- [x] 1.4 `alembic/versions/003_attack_surface.py` migration + model imports in `alembic/env.py`
- [x] 1.5 RLS enable + `tenant_isolation` policy for assets/scans/findings in `database.py`
- [x] 1.6 `dnspython==2.8.0` in `requirements.txt`
- [x] 1.7 RED test `tests/test_asm.py` (upsert + persistence on SQLite)

---

## PR 2 — Discovery Services (Phase 2) [complete]

### Work Unit Evidence

| Evidence | Required value |
|---|---|
| Focused test command + result | `cd backend && python -m pytest tests/test_discovery.py -v` → **13 passed** (crt.sh/dns/fingerprint). |
| Full-suite regression | `cd backend && python -m pytest tests/ -q` → **49 passed, 2 skipped** (RLS SQLite skips). |
| Runtime harness | `N/A` — pure discovery modules; orchestration/DB boundary is Phase 3. |
| Rollback boundary | Delete `backend/app/services/` (unused, no wiring yet) + revert `tasks.md` checkboxes. |

### Completed Tasks (Phase 2)

- [x] 2.1 `backend/app/services/__init__.py` — service package marker
- [x] 2.2 `services/enumerate.py` — `enumerate_subdomains(domain, http)` crt.sh GET `?q=%25.{domain}&output=json`, parse/dedupe hostnames, partial-fail on timeout/error
- [x] 2.3 RED test — crt.sh parse/dedupe + `crt.sh unavailable` → partial (mocked `httpx.AsyncClient`)
- [x] 2.4 `services/dns.py` — `resolve(hostname, resolver)` dnspython A/AAAA per-query timeout; NXDOMAIN/NoAnswer → empty, skip unresolvable
- [x] 2.5 `services/fingerprint.py` — httpx probe (status/server/title/x-powered-by) + ssl CN/SAN → fingerprint dict + candidate findings
- [x] 2.6 RED test — fingerprint extraction + unreachable host skipped (mock httpx/ssl)

### Files Changed (PR 2)

| File | Action | Description |
|------|--------|-------------|
| `backend/app/services/__init__.py` | Created | Package marker + module docstring |
| `backend/app/services/enumerate.py` | Created | crt.sh passive enumeration + dedupe + partial-fail |
| `backend/app/services/dns.py` | Created | dnspython A/AAAA resolve, NXDOMAIN/NoAnswer tolerant |
| `backend/app/services/fingerprint.py` | Created | HTTP/TLS fingerprint via httpx + ssl |
| `backend/tests/test_discovery.py` | Created | 13 unit tests (mock crt.sh/dns/httpx/ssl) |
| `openspec/changes/attack-surface-core/tasks.md` | Modified | Phase 2 tasks marked `[x]` (cumulative) |

### Deviation from Design (PR 2)

design.md/tasks.md planned modules under `backend/app/services/discovery/`
(crtsh.py, dns.py, fingerprint.py, orchestrator.py). The orchestrator's PR 2
launch prompt explicitly directed flat paths `backend/app/services/enumerate.py`,
`dns.py`, `fingerprint.py`. Followed the orchestrator's authoritative slice
definition. No orchestration layer added (Phase 3).

### Out of Scope (PR 2)

- No DB writes, no routes (`routes/asm.py` untouched), no config knobs (Phase 3).
- No frontend (Phase 4).
- Fingerprint returns candidate findings for the orchestrator to persist in Phase 3.

---

## PR 3 — Orchestration + API (Phase 3) [complete]

### Work Unit Evidence

| Evidence | Required value |
|---|---|
| Focused test command + result | `cd backend && python -m pytest tests/test_asm.py -v` → **13 passed** (7 new Phase-3 API tests: scan lifecycle, upsert no-dup, cross-tenant 404/empty, error status, 401 unauth). `cd backend && pytest tests/test_asm.py -k "scan or isolation"` green. |
| Full-suite regression | `cd backend && python -m pytest` → **56 passed, 2 skipped** (RLS SQLite skips). |
| Runtime harness | Real `POST /asm/scans` + token flow exercised end-to-end in tests via ASGITransport with mocked external services; orchestrator applies bounded timeouts from `config.settings`. |
| Rollback boundary | Revert `routes/asm.py` + `services/orchestrator.py` + `config.py` knobs; tests revert with `test_asm.py`. Additive, no data loss (assets/scans/findings tables remain). |

### Completed Tasks (Phase 3)

- [x] 3.1 `backend/app/services/orchestrator.py` — `async run_scan(db, tenant_id, domain)`: create Scan(running) → crt.sh enumerate → per-subdomain DNS resolve + fingerprint → upsert Asset (preserve `first_seen`, bump `last_seen`) → persist Findings → Scan `completed`/`error` + `completed_at`. `try/except` sets `error` on any failure; run_scan never raises.
- [x] 3.2 RED test — `POST /asm/scans` persists scan+assets+findings, upsert no-dup (preserves first_seen), discovery failure → `error` status.
- [x] 3.3 Rewrite `backend/app/routes/asm.py` — `ScanCreate{domain}` body + `get_current_user` dep; `POST /asm/scans` (sync → `{scan, assets}`); `GET /asm/assets` tenant-filtered; `GET /asm/results/{scan_id}` tenant-filtered else 404. Uses `user.tenant_id` from authenticated user for app-level isolation.
- [x] 3.4 `config.py` knobs — `dns_timeout`, `http_timeout`, `fingerprint_port`, `fingerprint_scheme` (all consumed by `run_scan`).
- [x] 3.5 RED e2e — 401 unauth on `POST /asm/scans` (invalid token) creates nothing; cross-tenant `GET /asm/results` → 404 (two tenants).

### Files Changed (PR 3)

| File | Action | Description |
|------|--------|-------------|
| `backend/app/services/orchestrator.py` | Created | `run_scan` wiring pure services into DB persistence; Scan lifecycle + Asset upsert + Finding persistence |
| `backend/app/services/__init__.py` | Modified | Docstring documents `orchestrator` module |
| `backend/app/routes/asm.py` | Modified | Auth-protected `POST /asm/scans`, `GET /asm/assets`, `GET /asm/results/{scan_id}` + DTOs |
| `backend/app/config.py` | Modified | Scan timeout / fingerprint knobs |
| `backend/tests/test_asm.py` | Modified | 7 Phase-3 integration tests (mocked discovery via orchestrator module monkeypatch) |
| `openspec/changes/attack-surface-core/tasks.md` | Modified | Phase 3 tasks marked `[x]` (cumulative) |

### Deviations from Design (PR 3)

- design.md listed `get_tenant_context` as a dependency; the codebase's actual dependency is `get_current_user` (auth.py), whose `user.tenant_id` provides the tenant. The step-name `get_tenant_context` was treated as a design shorthand; the real, existing `get_current_user` was used for consistency with the rest of the app.
- The `Scan` status verb is `completed` (not the spec's `complete`), matching the Phase-1 model default and the existing `test_scan_lifecycle_to_completed` convention.
- The crt.sh URL/timeout and TLS timeout are fixed in the Phase-2 discovery modules by design (not duplicated into `config.py`); config exposes only the knobs the orchestrator actually consumes.

### Out of Scope (PR 3)

- No frontend (Phase 4): `lib/api.ts`, attack-surface page, dashboard page untouched.
- No `main.py` change needed — `asm.router` already registered; new deps are imported inside `asm.py`.

---

## PR Boundary / Workload (cumulative)

- Mode: chained PR slice (feature-branch-chain). PR 1, PR 2 and PR 3 complete.
- PR 1 boundary: models + migration + RLS + dnspython pin (p1 branch).
- PR 2 boundary: discovery services (crt.sh + DNS + HTTP/TLS fingerprint) + tests (p2 branch).
- PR 2 review budget: 663 additions / 6 deletions (~669 changed lines).
- PR 3 boundary: orchestrator + /asm API + config knobs (p3 branch). 413 additions /
  20 deletions tracked (~433) + new `orchestrator.py` (~200 lines).
- Remaining PR: PR 4 (frontend: lib/api.ts asm namespace + attack-surface + dashboard pages).
