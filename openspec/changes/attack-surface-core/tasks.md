# Tasks: Attack Surface Manager — Sprint 1 Core

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 1200–1600 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 → PR 2 → PR 3 → PR 4 (feature-branch chain) |
| Delivery strategy | ask-on-risk |
| Chain strategy | feature-branch-chain |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Asset/Scan/Finding models + migration + RLS + dnspython pin | PR 1 (base=feature tracker) | `cd backend && pytest tests/test_asm.py -k upsert` | `cd backend && alembic upgrade head && alembic downgrade 002` | Drop `assets`/`scans`/`findings` tables; additive |
| 2 | crt.sh + DNS + fingerprint discovery modules | PR 2 (base=PR1) | `cd backend && pytest tests/test_asm.py -k "enumeration or fingerprint"` | N/A — pure logic, mocked `httpx`/`dns.resolver` | Delete `services/discovery/`; unused, no wiring |
| 3 | Orchestrator + auth /asm routes + config knobs | PR 3 (base=PR2) | `cd backend && pytest tests/test_asm.py -k "scan or isolation"` | real `POST /asm/scans` via uvicorn + token | Revert `routes/asm.py` + `config.py` knobs |
| 4 | lib/api.ts asm namespace + dashboard + attack-surface pages | PR 4 (base=PR3) | `pnpm test` | `pnpm dev` browse `/dashboard` | Revert frontend files to static zeros |

## Phase 1: Data Foundation

- [x] 1.1 Create `backend/app/models/asset.py` with `Asset` (CoercingUuid id, `tenant_id` FK, domain, subdomain, ip, port, service, fingerprint JSON, status, first_seen, last_seen, discovered_at; `UniqueConstraint(tenant_id, subdomain)`)
- [x] 1.2 Add `Scan` (id, tenant_id FK, domain, status, started_at, completed_at) and `Finding` (id, tenant_id, asset_id, scan_id, severity, title, detail, discovered_at) to `asset.py`
- [x] 1.3 Register `Asset`, `Scan`, `Finding` in `backend/app/models/__init__.py`
- [x] 1.4 Create `backend/alembic/versions/003_attack_surface.py` (down_revision `002_tenant_id_not_null`): create 3 tables + composite index + FK indexes
- [x] 1.5 Add RLS `ENABLE` + `tenant_isolation` policy (users/tenants superadmin pattern) for `assets`/`scans`/`findings` in `backend/app/database.py` `init_db` try-block
- [x] 1.6 Add `dnspython==2.8.0` to `backend/requirements.txt`
- [x] 1.7 RED test: `tests/test_asm.py` re-scan upsert (preserve first_seen, no dup) + models persist — SQLite conftest `client`

## Phase 2: Discovery Services

> Note (PR 2 deviation): the orchestrator's launch prompt places these modules
> directly under `backend/app/services/` (`enumerate.py`, `dns.py`,
> `fingerprint.py`) rather than the planning `services/discovery/` subpackage
> named below. All six Phase-2 tasks are implemented at the orchestrator-specified
> paths. Persistence and orchestration remain out of scope (Phase 3).

- [x] 2.1 Create `backend/app/services/__init__.py` service package marker
- [x] 2.2 `enumerate.py`: `enumerate_subdomains(domain, http)` → GET `?q=%25.{domain}&output=json`, parse/dedupe hostnames, do NOT abort on timeout/error (return partial + log)
- [x] 2.3 RED test: crt.sh parse/dedupe + `crt.sh unavailable` continues partial (mocked `httpx.AsyncClient`)
- [x] 2.4 `dns.py`: `resolve(hostname, resolver)` dnspython A/AAAA/CNAME with per-query timeout, returns live hostnames (skip unresolvable)
- [x] 2.5 `fingerprint.py`: httpx probe (status/server/title/x-powered-by) + ssl CN/SAN → fingerprint dict + candidate findings list
- [x] 2.6 RED test: fingerprint extraction + unresolvable host skipped (mock `dns.resolver`/`httpx`)

## Phase 3: Orchestration + API

- [x] 3.1 `orchestrator.py`: `async run_scan(db, tenant_id, domain)` — passive → active → upsert `Asset` (preserve first_seen) → persist `Finding` → `Scan` status complete/error + completed_at
- [x] 3.2 RED test: `POST /asm/scans` persists scan+assets+findings, upsert no-dup, error→`error` status
- [x] 3.3 Rewrite `backend/app/routes/asm.py`: `ScanCreate{domain}` body, add `get_tenant_context`+`get_current_user` deps; `POST /asm/scans` sync → `{scan, assets}`; `GET /asm/assets` tenant-filtered; `GET /asm/results/{scan_id}` tenant-filtered else 404
- [x] 3.4 Add scan timeout/concurrency/rate-limit knobs to `backend/app/config.py` Settings
- [x] 3.5 RED e2e: 401 unauth on `POST /asm/scans`; cross-tenant `GET /asm/results` → 404 isolation (two tenants)

## Phase 4: Frontend Wiring

- [x] 4.1 Update `lib/api.ts` `asm` namespace: typed `list()`, `scan(domain)` (POST /asm/scans), `results(scanId)`; remove `scan(assetId)`
- [x] 4.2 RED test: `lib/api.test.ts` covers typed `asm` fetch contract (mock fetch)
- [x] 4.3 `app/dashboard/attack-surface/page.tsx`: fetch real assets + start scan via `api.asm`
- [x] 4.4 `app/dashboard/page.tsx`: real asset/finding/scan counts from `api.asm`
- [x] 4.5 Verify `pnpm lint` + `tsc --noEmit` pass; run full `pnpm test && cd backend && pytest` green
