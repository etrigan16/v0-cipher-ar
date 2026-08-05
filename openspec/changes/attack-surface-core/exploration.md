## Exploration: attack-surface-core — Attack Surface Manager (Sprint 1)

### Current State

The Attack Surface module is entirely a STUB today. Nothing is discoverable, scannable, or persisted.

**Backend** (`backend/`):
- `backend/app/routes/asm.py` — router `prefix="/asm"` with three placeholder handlers that return hardcoded empties:
  - `GET /asm/assets` → `{"assets": []}`
  - `POST /asm/scan/{asset_id}` → `{"scan_id": "placeholder", "status": "queued"}`
  - `GET /asm/results/{scan_id}` → `{"findings": []}`
- No `Asset` / `Finding` / `Scan` models. `backend/app/models/__init__.py` exports only `Tenant`, `User`, `WaitlistEntry`. Every model uses a shared `CoercingUuid` UUID type (portable across PostgreSQL native UUID and SQLite CHAR(32)).
- Multi-tenant RLS is established: `User.tenant_id` FK NOT NULL, `Tenant` model exists, middleware `backend/app/middleware/tenant.py` (`get_tenant_context`) decodes JWT `tenant_id`, runs `SET LOCAL app.current_tenant_id`, `SET LOCAL app.current_user_id`, and sets `request.state.current_tenant_id`. RLS policies are created in `database.py::init_db` for `users`, `tenants`, `waitlist_entries` (PostgreSQL only; SQLite silently skips).
- Auth: JWT (HS256) with `tenant_id` + `sub` claims (`routes/auth.py::create_access_token`); `get_current_user` resolves `User`. `SECRET_KEY` and `RESEND_API_KEY` are required settings (`config.py`).
- Dependency versions (`requirements.txt`): fastapi 0.115.6, sqlalchemy 2.0.36 async, asyncpg 0.30.0, aiosqlite 0.22.1, httpx 0.28.1 (test), pydantic 2.10.3, alembic 1.18.5. **`dnspython` is installed in the environment (2.8.0) but is NOT in `requirements.txt`** — must be added for active DNS resolution.
- Migrations: Alembic (`backend/alembic/versions/001_tenants.py`, `002_tenant_id_not_null.py`). Alembic init and env wiring are present (untracked working-tree changes suggest recent setup).
- No Redis/Celery/background task infra exists today. `docker-compose.yml` runs only `backend` + `caddy`. No queue layer for async scans.
- Test harness: `backend/tests/conftest.py` uses in-memory SQLite with `override_get_db`. RLS tests must skip on SQLite (documented). No `httpx`-mock-based external API test pattern yet; `test_waitlist.py` uses `AsyncMock` + monkeypatch for Resend.

**Frontend** (`app/`, `lib/`):
- `app/dashboard/attack-surface/page.tsx` — fully static "use client" page: domain/IP input (no submit handler), hardcoded "ACTIVOS MONITOREADOS: 0", and an empty-state body. No data fetch.
- `app/dashboard/page.tsx` — dashboard with four hardcoded stat cards all `"0"`; no API call.
- `lib/api.ts` — has an `asm` namespace already: `list` → `/asm/assets`, `scan(assetId)` → `POST /asm/scan/{assetId}`, `results(scanId)` → `/asm/results/{scanId}`, returning `{ assets: unknown[] }` etc. Auth via Bearer token from localStorage. `next.config.mjs` rewrites `/api/backend/*` to the API origin.
- `app/dashboard/layout.tsx` — already has an "Attack Surface" sidebar link.

**Product scope** (from `wiki/projects/aukalabs/sprint-1-attack-surface.md` + `plan-mvp.md`):
- Sprint 1 = subdomain enumeration, cloud discovery, fingerprinting, API scans. Sprint 2 = risk scoring + LLM enrichment + dashboard + export (deferrable).
- Wiki's `modelos/asset.py` proposes an `Asset` flattened model; `API Endpoints` table proposes `/api/v1/...` nested paths (but the live API convention uses bare prefixes — `asm.router` has no `/api/v1`).
- Sprint-0 wiki shows RLS applied to `assets` — the pattern to follow.

### Affected Areas

| File | Why affected |
|------|-------------|
| `backend/app/models/asset.py` | NEW — `Asset` model (and likely `Finding`, `Scan`/`ScanResult`) |
| `backend/app/models/__init__.py` | Import/register the new models |
| `backend/app/database.py` | Register models in `init_db`; add RLS `ENABLE` + policy for `assets` (and findings) |
| `backend/app/routes/asm.py` | Replace stub handlers; add auth dependency + real queries; add `POST /asm/scans` (domain-based) |
| `backend/app/routes/__init__.py` | (no change likely) |
| `backend/alembic/versions/00X_assets.py` | NEW migration(s) for `assets`/`findings`/`scan_results` + RLS policies |
| `backend/app/services/discovery/…` | NEW — passive (crt.sh) + active (DNS resolve) + HTTP probe + fingerprint + cloud helpers |
| `backend/requirements.txt` | Add `dnspython` for active DNS resolution |
| `backend/app/config.py` | Maybe add a few knobs (e.g. default scan timeouts, rate-limit window) |
| `backend/tests/test_asm.py` | NEW — API tests with mocked external sources (crt.sh/httpx), SQLite fixtures |
| `backend/tests/conftest.py` | Possibly add asset models to test schema (already creates all via `Base.metadata`) |
| `lib/api.ts` | Extend `asm` namespace types + new endpoints (domain-scan, findings) |
| `app/dashboard/attack-surface/page.tsx` | Real data fetch (asset list + start scan) replacing hardcoded zeros |
| `app/dashboard/page.tsx` | Wire real asset/finding/scan counts for tenant |
| `app/dashboard/attack-surface/` (components) | NEW — asset table / row / empty states |

### Approaches

**Domain model shape**

1. **Flat `Asset` table only (minimal)** — single normalized row per discovered hostname/IP carrying domain, hostname, ip, service, fingerprint (JSON), cloud_provider, status, discovered_at. Findings embedded not modelled yet.
   - Pros: Smallest Sprint-1 surface; matches wiki's proposed `Asset` model; easy RLS; Fast.
   - Cons: Re-scans overwrite/update in place; no audit history of findings; limits Sprint 2 risk scoring.
   - Effort: **Low**

2. **`Asset` + `Finding` + `Scan`/`ScanResult` (recommended baseline for the MVP)**
   - `Asset` = discovered entity (per tenant). `Finding` = issue on an asset (type like open_port/outdated_ssl/tls_issue, severity, cvss, description, remediation). `Scan` = a discovery run storing status + timestamps + optional result summary.
   - Pros: Matches the wiki's `models/finding.py` and Sprint 2 risk-scoring needs; distinct scans; audit trail; stable API contract for later report/export. Findings table already has concrete wiki shape.
   - Cons: More tables/migrations; more tests.
   - Effort: **Medium**

**Enumeration strategy**

3. **Passive-first OSINT (recommended)** — query Certificate Transparency logs via **crt.sh API** (`https://crt.sh/?q=%25.{domain}&output=json`), deduplicate hostnames, then optionally `wayback` CDX later. No API key required.
   - Pros: Free, no keys, single HTTP call per domain, huge coverage, trivially mockable in tests (httpx mocked).
   - Cons: Rate limits / slowness on big domains; results depend on cert issuance history (misses non-cert subdomains).
   - Effort: **Low**

4. **Active DNS enumeration** — brute-force wordlists against `dns.resolver` (dnspython) to discover subdomains not in cert logs; plus resolve `A`/`AAAA`/`CNAME` for found hostnames and HTTP-probe live hosts.
   - Pros: Finds non-cert assets (staging, internal-ish); gives IPs for fingerprinting; active resolution is core to the wiki.
   - Cons: Slow, noisy on large wordlists; dnspython must be added to requirements; needs careful timeouts.
   - Effort: **Medium**

**Exposure / fingerprinting**

5. **HTTP probe + header/TLS fingerprint (recommended)** — for each resolved host, `httpx` GET (or hand-rolled `httpx.Client`) collecting status, `server` header, title, `x-powered-by`, redirect chain; light TLS-cert subject/issuer via `ssl`/`cryptography`; common-port set (80/443/8080/8443/3000/5000/9000). No Wappalyzer dependency — a small local regex/dict maps headers→tech.
   - Pros: Fully offline/self-contained; mockable; no heavy deps; covers "Fingerprinting" DoD.
   - Cons: Wappalyzer-scale fingerprint coverage is shallow without the full signature DB.
   - Effort: **Medium**

**Cloud discovery**

6. **Defer full AWS/Azure/GCP provider APIs to Sprint 2 (recommended for scope safety)** — the wiki lists cloud APIs (boto3 etc.) but Sprint 1 DoD emphasizes subdomain enum + fingerprinting + API scans. Cloud discovery adds heavy per-provider auth, SDK deps, and free-tier complexity.
   - Pros: Keeps Sprint 1 shippable; the plan explicitly defers risk scoring + LLM to Sprint 2 anyway.
   - Cons: Doesn't reach the "Clouds AWS/Azure/GCP descubren assets" DoD checkbox in Sprint 1.
   - Effort: If included — **High**; if deferred — **None now**

**API / scan orchestration**

7. **Synchronous scan endpoint with light scaling (recommended)** — `POST /asm/scans` takes `{domain}`, runs passive+active discovery inline (bounded concurrency, timeouts), writes `Asset` rows + `Scan`, returns the scan + assets. Add a DB-backed `Scan.status` (`queued|running|complete|error`) even if runs synchronously first, so Sprint 2 can swap in Celery/Redis later without changing the API contract.
   - Pros: Simple, testable with SQLite; no infra; API contract future-proof.
   - Cons: Long-running request under real load (mitigate via reasonable timeouts); no cross-instance queue yet.
   - Effort: **Low-Medium**

**Multi-tenant enforcement**

8. **RLS on new tables + tenant-scoped reads (recommended, matches existing pattern)** — add `tenant_id` FK to `Asset` (and `Finding`), include the new tables in `database.py::init_db` `ENABLE ROW LEVEL SECURITY` + `CREATE POLICY tenant_isolation` block (mirroring `waitlist_entries`), and write routes that inject `get_tenant_context` and filter by `request.state.current_tenant_id`. For testability, use the existing SQLite fixture and skip RLS tests (as the project already does), while keeping app-level tenant filtering so SQLite integration tests can still assert cross-tenant isolation.
   - Pros: Defense-in-depth (DB RLS in prod + app filter); consistent with every data table so far; SQLite tests remain green.
   - Cons: Must remember app-level filter too (double maintenance); RLS-specific behavior only verified in staged Postgres.
   - Effort: **Low**

### Recommendation

Combine **#2 (Asset+Finding+Scan model)** + **#3 passive-first crt.sh** + **#4 light active DNS (dnspython)** + **#5 HTTP/TLS fingerprint** + **defers cloud provider APIs to Sprint 2 (#6)** + **#7 sync scan endpoint with forward-compatible Scan.status** + **#8 RLS + app-filter**.

Rationale:
- The repo's stated truth (`plan-mvp.md`, `sprint-1-attack-surface.md`) splits Sprint 1 (enum/cloud/fingerprint/API scans) from Sprint 2 (risk scoring/LLM/dashboard/export). Shipping a **passive + active subdomain discovery with DNS resolution and HTTP/TLS fingerprinting, persisted into `Asset` (+ `Scan`) with findings-ready shape**, is the right slice that reaches multiple DoD checkboxes (subdomains from OSINT, HTTP probe identifies live hosts, fingerprint detects technologies, RLS isolates tenants) without taking on cloud-SDK and LLM/complexity this iteration.
- The `/asm/*` path prefix is already the live convention (`lib/api.ts` uses it); keep it rather than introducing the wiki's aspirational `/api/v1/scans/...` paths, to avoid a frontend/backend contract mismatch. Extend the existing `asm` router + `api.asm` client.
- Reuse the established `CoercingUuid` and RLS policy approach verbatim for consistency.
- `dnspython` is already present in the runtime env but must be pinned into `requirements.txt` (currently absent) — a genuine gap the proposal should close.
- **Defer cloud asset discovery** (AWS/Azure/GCP SDKs) and **risk scoring / LLM enrichment / export** — the plan already places these in Sprint 2, and including them now would blow the 400-line review budget and add infra (SDKs, queue, LLM gateway) not needed for the Sprint 1 DoD.

### Risks

- **crt.sh reliability**: external service can be slow or rate-limit. Mitigate: cache results per domain, generous timeout, treat source failure as partial (log + continue with DNS) rather than failing the scan.
- **dnspython missing from `requirements.txt`**: present in the local env but not pinned — the change MUST add it or CI (`pytest`) and prod image break at import time.
- **Active DNS scope/noise**: brute-force enums can be slow and flag internal names. Use a conservative wordlist, per-query timeout, and concurrency cap; keep DNS optional/paranoid defaults.
- **RLS testability**: RLS policies can't be exercised on the SQLite test fixture. Rely on app-level tenant filtering for SQLite integration assertions and document the Postgres-only RLS check (existing project convention).
- **Review budget**: Sprint-1 core (models + migration + discovery services + routes + tests + frontend wiring) is large. Recommend the proposal/tasks slice into logical work units and forecast whether chained PRs are needed against the 400-line budget.
- **Long-running scans**: synchronous scans can block the FastAPI worker. Bound timeouts and per-host concurrency; the `Scan.status` field leaves a clean path to Celery/Redis later.
- **Storage growth / in-place rescans**: re-running discovery should upsert (keep `first_seen`, update `last_seen`) to avoid unbounded duplicate `Asset` rows per tenant.

### Ready for Proposal

**Yes.** The exploration is complete and concrete. The orchestrator should tell the user:
- Recommended scope is **passive (crt.sh) + light active (DNS/HTTP/TLS) discovery** persisted into an `Asset`+`Scan` (+findings-shaped) model, tenant-isolated via RLS + app filter, exposed through the existing `/asm` router and `api.asm` client, real data wired into the attack-surface and dashboard pages.
- **Explicitly deferred to Sprint 2**: cloud-provider API discovery, risk scoring, LLM enrichment, export.
- **Authors the proposal must settle**: (a) confirm the deferred cloud/risk/export stance; (b) add `dnspython` to `requirements.txt`; (c) decide whether `Finding` is created now (Sprint 1) or in Sprint 2; (d) keep the `/asm` prefix vs migrate to wiki's `/api/v1/scans/...` paths.
