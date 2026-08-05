# Proposal: Attack Surface Manager — Sprint 1 Core

## Intent

The Attack Surface module is a stub: `/asm` returns hardcoded empties and the dashboard shows static zeros. This change ships the Sprint 1 core — discover, fingerprint, and persist a tenant's external attack surface — and wires real data into the frontend. It enables passive (crt.sh) subdomain enumeration plus active DNS/HTTP/TLS fingerprinting, tenancy-isolated via RLS + app filter.

## Scope

### In Scope
- `Asset`, `Scan`, `Finding` SQLAlchemy models (reuse `CoercingUuid`, `tenant_id` FK).
- Alembic migration(s) for new tables + RLS `ENABLE` + `tenant_isolation` policies.
- Passive discovery: crt.sh CT-log subdomain enumeration (`?q=%25.{domain}&output=json`).
- Active discovery: dnspython DNS resolve (A/AAAA/CNAME) + HTTP/TLS fingerprint (httpx, status/title/server/x-powered-by, TLS subject/issuer).
- `/asm` API: list assets, `POST /asm/scans` (domain-based, sync), scan results/findings.
- `lib/api.ts` `asm` namespace typed extension.
- Basic discoverability: populate asset list + tenant counts on attack-surface and dashboard pages.
- Pin `dnspython` in `requirements.txt`.
- `tests/test_asm.py` with mocked external sources (httpx) over SQLite.

### Out of Scope (Sprint 2)
- Cloud SDKs (AWS/Azure/GCP) discovery, risk scoring / LLM enrichment, PDF/text export, advanced dashboard (charts, insights).

## Capabilities

### New Capabilities
- `<attack-surface>`: Asset/Scan/Finding models, passive+active discovery, `/asm` API, and basic tenant dashboard wiring.

### Modified Capabilities
- None (no existing capability requirement changes; RLS extension is internal to new tables).

## Approach

Follow exploration recommendation: `Asset`+`Scan`+`Finding` model; passive-first crt.sh; light active DNS (dnspython) + HTTP/TLS fingerprint; sync scan endpoint with forward-compatible `Scan.status` (queued|running|complete|error) so Sprint 2 can swap in Celery without changing the contract; RLS + app-level tenant filter mirroring `waitlist_entries`. Keep the `/asm` prefix to preserve the live frontend/CI contract. Upsert assets on re-scan (keep `first_seen`, update `last_seen`) to avoid unbounded rows.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/models/asset.py` | New | `Asset`, `Scan`, `Finding` models |
| `backend/app/models/__init__.py` | Modified | Register new models |
| `backend/app/database.py` | Modified | RLS ENABLE + policy for `assets`/`findings`/`scans` |
| `backend/alembic/versions/00X_assets.py` | New | Migration(s) + RLS |
| `backend/app/services/discovery/` | New | crt.sh, DNS, HTTP/TLS fingerprint modules |
| `backend/app/routes/asm.py` | Modified | Real auth-protected handlers + `POST /asm/scans` |
| `backend/app/routes/__init__.py` | Modified | Register scan/service deps if needed |
| `backend/app/config.py` | Modified | Scan timeout / concurrency / rate-limit knobs |
| `backend/requirements.txt` | Modified | Add `dnspython==2.8.0` |
| `backend/tests/test_asm.py` | New | Mocked-source API tests |
| `lib/api.ts` | Modified | Typed `asm` namespace |
| `app/dashboard/attack-surface/page.tsx` | Modified | Real fetch + start scan |
| `app/dashboard/page.tsx` | Modified | Real asset/finding/scan counts |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| crt.sh rate-limit/slowness | Med | Cache per domain, generous timeout, treat source failure as partial |
| Scan blocks worker | Med | Bound timeouts + per-host concurrency; `Scan.status` future-proofs queue |
| RLS untestable on SQLite | High | App-level tenant filter + skip RLS tests (existing convention) |
| >400-line review budget | High | Chained PRs across work units |
| DNS enum noise/slowness | Medium | Conservative wordlist, per-query timeout, paranoid defaults |

## Rollback Plan

Revert by removing `attack-surface`/`asm` migration(s); new tables are additive so rolling back the migration (or leaving tables) drops no existing tenant/user data. Frontend wiring rolls back by restoring prior static pages. `requirements.txt` dnspython pin is inert to revert.

## Dependencies

- `dnspython` (pin in `requirements.txt`; already in env).
- crt.sh external API (no key).
- `httpx` (already present) for HTTP probe + mocking in tests.

## Success Criteria

- [ ] `POST /asm/scans` persists `Asset`/`Scan`/`Finding` rows per tenant; re-scan upserts (no duplicates).
- [ ] RLS enabled for new tables in PostgreSQL; app filter proves cross-tenant isolation in SQLite tests.
- [ ] Attack-surface page lists real assets; dashboard shows real counts.
- [ ] `cd backend && pytest` and `pnpm test` green.
