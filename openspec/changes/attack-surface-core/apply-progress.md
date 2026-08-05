# Apply Progress: attack-surface-core — PR 1 + PR 2 + PR 3 + PR 4

**Status**: ALL PHASES COMPLETE (23/23 tasks). Ready for verify/archive.
**Mode**: Standard (tests written alongside each work unit; no strict TDD gate).
**Delivery strategy**: chained (feature-branch-chain) — 4 PRs. PR 1, PR 2, PR 3, PR 4 done.
**PR 1 branch**: `feature/attack-surface-core-p1` (targeted tracker `feature/attack-surface-core`).
**PR 2 branch**: `feature/attack-surface-core-p2` (base = p1 branch).
**PR 3 branch**: `feature/attack-surface-core-p3` (base = p2 branch).
**PR 4 branch**: `feature/attack-surface-core-p4` (base = p3 branch). **CURRENT**.

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

## PR 4 — Frontend Wiring (Phase 4) [complete] ← CURRENT SLICE

### Work Unit Evidence

| Evidence | Required value |
|---|---|
| Focused test command + result | `pnpm test lib/api.test.ts app/dashboard/attack-surface/page.test.tsx` → **15 passed** (4 new `api.asm` contract tests + 4 attack-surface page tests + existing 7). |
| Full-suite frontend regression | `pnpm test` → **30 passed, 8 failed** (the 8 failures are pre-existing in `app/dashboard/mfa/page.test.tsx` + `app/login/page.test.tsx`; confirmed identical on base `p3` via `git stash` — NOT introduced by PR 4). |
| Full-suite backend regression | `cd backend && python -m pytest tests/ -q` → **56 passed, 2 skipped** (unchanged, green). |
| Runtime harness | `pnpm dev` browse `/dashboard/attack-surface`: assets fetched via `GET /asm/assets`, scan via `POST /asm/scans`, table + scan status render; static-zero placeholders replaced. |
| Rollback boundary | Revert `lib/api.ts` asm namespace + `lib/api.test.ts` asm describe + `app/dashboard/attack-surface/page.tsx` (+`page.test.tsx`) + `app/dashboard/page.tsx` → returns to static zeros. Frontend-only; no backend/data impact. |

### Completed Tasks (Phase 4)

- [x] 4.1 `lib/api.ts` — `asm` namespace rewritten to match backend contract: `listAssets()` → GET /asm/assets, `scanDomain(domain)` → POST /asm/scans `{domain}`, `getResults(scanId)` → GET /asm/results/{scan_id}; old `scan(assetId)` (POST /asm/scan/{id}) removed. Added exported `Asset`/`Scan`/`Finding` types.
- [x] 4.2 RED test — `lib/api.test.ts` adds `describe("api.asm")`: typed fetch contract for `listAssets`/`scanDomain`/`getResults` (URL, method, body) + error propagation (mock fetch).
- [x] 4.3 `app/dashboard/attack-surface/page.tsx` — fetches real assets on mount via `api.asm.listAssets()`; renders asset table (subdomain, ip, port, service, fingerprint title, status, discovered date) + monitored-asset count; domain input form triggers `api.asm.scanDomain(domain)` with loading state, scan status display, and asset refresh after scan; empty/error/loading states.
- [x] 4.4 `app/dashboard/page.tsx` — "Activos monitoreados" card wired to real `api.asm.listAssets()` count (loading `…`, fallback `0` on error); dashboard CTA now links to `/dashboard/attack-surface`.
- [x] 4.5 Final gate — `pnpm exec tsc --noEmit` → clean (0 errors); `pnpm lint` → **0 errors, 7 warnings (all pre-existing** in untouched files: mfa page, auth-context, ui/carousel, ui/sidebar, use-mobile, hooks/use-mobile); full `pnpm test` + `cd backend && pytest` verified (see evidence above).

### Files Changed (PR 4)

| File | Action | Description |
|------|--------|-------------|
| `lib/api.ts` | Modified | `asm` namespace → `listAssets`/`scanDomain`/`getResults`; exported `Asset`/`Scan`/`Finding` types |
| `lib/api.test.ts` | Modified | `describe("api.asm")` — 4 mocked-fetch contract tests |
| `app/dashboard/attack-surface/page.tsx` | Modified | Real assets fetch + table + scan form + status + refresh |
| `app/dashboard/attack-surface/page.test.tsx` | Created | 4 page tests (mock fetch): lists assets, shows count, starts scan + refresh, error state |
| `app/dashboard/page.tsx` | Modified | Real asset count stat card + CTA link to attack-surface |
| `openspec/changes/attack-surface-core/tasks.md` | Modified | Phase 4 tasks marked `[x]` (all 23 complete) |

### Deviations from Design / Prompt (PR 4)

- Method names: tasks.md/prompt said typed `list()`, `scan(domain)`, `results(scanId)`; implemented as `listAssets()`, `scanDomain(domain)`, `getResults(scanId)` — the launch prompt's own task-1 wording (`scanDomain(domain)`, `listAssets()`, `getResults(scanId)`) is authoritative and self-consistent with the backend DTOs.
- Asset `discovered_at` (listed in spec's model table) does not exist on the Phase-1 `Asset` model — the model uses `first_seen`/`last_seen` only. The page renders the "Descubierto" column from `first_seen`. This is a pre-existing Phase-1 deviation, not introduced here.
- Dashboard stat wiring: only "Activos monitoreados" is wired to real data (feasible from `GET /asm/assets`); findings/scans counts would require a new backend endpoint, out of scope for this slice. Other cards keep static zeros (unchanged behavior).
- GET-request tests assert `options.method ?? "GET"` because `request()` does not set `method` on GET (fetch default), matching the existing `auth.me`/waitlist test convention.

### Issues Found (PR 4)

- Pre-existing frontend test failures: `app/dashboard/mfa/page.test.tsx` (4) and `app/login/page.test.tsx` (4) fail on base branch `p3` too (verified by `git stash`). Out of scope for this slice; noted for verify phase.

---

## PR Boundary / Workload (cumulative)

- Mode: chained PR slice (feature-branch-chain). All 4 PRs complete (23/23 tasks).
- PR 1 boundary: models + migration + RLS + dnspython pin (p1 branch).
- PR 2 boundary: discovery services + tests (p2 branch). ~669 changed lines.
- PR 3 boundary: orchestrator + /asm API + config knobs (p3 branch). 413/20 tracked + new orchestrator.py (~200).
- PR 4 boundary: frontend wiring (p4 branch). `lib/api.ts` (+~60/-10), `lib/api.test.ts` (+~90), attack-surface page (+~140), new page.test.tsx (+~100), dashboard page (+~30).
- Final: `feature/attack-surface-core` tracker aggregates p1→p4; full change ready for `sdd-verify`.
