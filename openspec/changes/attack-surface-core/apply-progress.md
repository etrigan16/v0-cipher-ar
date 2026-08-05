# Apply Progress: attack-surface-core — PR 1 (Data Foundation) + PR 2 (Discovery Services)

**Status**: Phase 1 + Phase 2 complete (13/13 tasks). Phases 3-4 deferred.
**Mode**: Standard (tests written alongside each work unit; no strict TDD gate).
**Delivery strategy**: chained (feature-branch-chain) — 4 PRs. PR 1 done, PR 2 done.
**PR 1 branch**: `feature/attack-surface-core-p1` (targeted tracker `feature/attack-surface-core`).
**PR 2 branch**: `feature/attack-surface-core-p2` (base = p1 branch).

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

## PR Boundary / Workload

- Mode: chained PR slice (feature-branch-chain). PR 1 and PR 2 complete.
- Current work unit (PR 2): discovery services (crt.sh + DNS + HTTP/TLS fingerprint).
- Boundary: starts after Phase-1 models (p1 branch) and ends with the three pure
  discovery modules + their tests; explicitly stops before orchestration/API.
- PR 2 review budget: 663 additions / 6 deletions (~669 changed lines), within the
  chained-slice scope as directed by the orchestrator.
- Remaining PRs: PR 3 (orchestrator + /asm routes + config knobs), PR 4 (frontend).
