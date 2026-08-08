# Design: Attack Surface Manager — Sprint 1 Core

## Technical Approach

Extend the `/asm` stub into a real, auth-protected attack-surface flow: passive crt.sh subdomain enumeration + active DNS/HTTP/TLS fingerprinting, persisted to new `Asset`/`Scan`/`Finding` tables, tenant-isolated via RLS + an app-level filter, and wired into a typed `lib/api.ts` client and the attack-surface/dashboard pages. Discovery runs synchronously with bounded timeouts; `Scan.status` (`queued|running|complete|error`) keeps the contract forward-compatible for a Sprint-2 queue. Every design choice mirrors existing conventions (`CoercingUuid`, `Base`, `database.py::init_db` RLS block, `get_tenant_context` middleware, `lib/api.ts` namespace pattern).

## Architecture Decisions

| Decision | Options | Tradeoff | Choice |
|---|---|---|---|
| Scan endpoint shape | `POST /asm/scan/{domain}` vs `POST /asm/scans` `{domain}` body | Stub uses path-param asset; spec+proposal use body domain | `POST /asm/scans` with `{domain}` body (spec is authoritative); drop `AssetResponse`-only listing |
| Upsert strategy | DELETE+reinsert vs SELECT-then-update vs composite-unique+`ON CONFLICT` | Dupe safety vs portability | Composite unique `(tenant_id, subdomain)` + select-then-update preserving `first_seen` |
| Sync vs async scan | Blocking in-route vs background task/Celery | Worker bloat vs simplicity + future queue | Synchronous in-route with bounded timeouts; `Scan.status` contains future queue state |
| DNS lib | `socket.gethostbyname` vs `dnspython` | Native A-only, blocking vs A/AAAA/CNAME + timeout | `dnspython==2.8.0` (pinned), per-query timeout |
| RLS on SQLite | Test real RLS vs app filter | PG-only support | App-level `tenant_id` filter in routes; RLS tests skip on SQLite (`pytest.skip`, existing convention) |
| Finding source | Derive in orchestrator vs separate fingerprint module | Coupling | Fingerprint module returns candidate findings; orchestrator persists them |

The launch scope header (`POST /asm/scan/{domain}`) is superseded: the spec and proposal consistently define `POST /asm/scans` with a `{domain}` body. The existing `lib/api.ts::scan(assetId)` and stub route are updated to this contract.

## Data Flow

```
POST /asm/scans {domain}  (get_tenant_context + get_current_user)
   │  create Scan(status=running, started_at)
   ▼
crt.sh ──GET ?q=%25.{domain}&output=json──▶ dedupe hostnames  (partial-fail tolerated)
   │
   ▼
dnspython A/AAAA/CNAME resolve ──▶ live hostnames (unresolvable skipped)
   │
   ▼
httpx probe (status/server/title/x-powered-by) + ssl cert (CN/SAN)
   │
   ▼
upsert Asset (preserve first_seen, bump last_seen) + persist Finding rows
   │
   ▼
Scan(status=complete|error, completed_at) ──▶ response {scan, assets}
GET /asm/assets ──▶ SELECT assets WHERE tenant_id=ctx.filter
GET /asm/results/{scan_id} ──▶ scan + findings WHERE tenant_id=ctx.filter (else 404)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/models/asset.py` | Create | `Asset`, `Scan`, `Finding` models (CoercingUuid, tenant FK, indexes) |
| `backend/app/models/__init__.py` | Modify | Register new models |
| `backend/app/database.py` | Modify | RLS ENABLE + `tenant_isolation` policy for `assets`/`scans`/`findings` |
| `backend/alembic/versions/003_attack_surface.py` | Create | Migrations + composite index + RLS |
| `backend/app/services/discovery/__init__.py` | Create | Package marker |
| `backend/app/services/discovery/crtsh.py` | Create | Passive crt.sh enumeration + dedupe |
| `backend/app/services/discovery/dns.py` | Create | dnspython A/AAAA/CNAME resolve |
| `backend/app/services/discovery/fingerprint.py` | Create | httpx HTTP probe + ssl TLS fingerprint + candidate findings |
| `backend/app/services/discovery/orchestrator.py` | Create | `run_scan` — Scan lifecycle, upsert, findings |
| `backend/app/routes/asm.py` | Modify | Real auth-protected handlers + `POST /asm/scans` |
| `backend/app/config.py` | Modify | Scan timeout/concurrency knobs |
| `backend/requirements.txt` | Modify | Add `dnspython==2.8.0` |
| `backend/tests/test_asm.py` | Create | Mocked crt.sh/dnspython/httpx, SQLite tenant-isolation |
| `lib/api.ts` | Modify | Typed `asm` namespace (`list`, `scan(domain)`, `results`) |
| `lib/api.test.ts` | Modify | Cover expanded `asm` namespace |
| `app/dashboard/attack-surface/page.tsx` | Modify | Fetch real assets + start scan |
| `app/dashboard/page.tsx` | Modify | Real asset/finding/scan counts |

## Interfaces / Contracts

```python
# routes/asm.py
class ScanCreate(BaseModel): domain: str
# GET /asm/assets -> {"assets": [AssetDTO]}
# POST /asm/scans (body ScanCreate) -> {"scan": ScanDTO, "assets": [AssetDTO]}
# GET /asm/results/{scan_id} -> {"scan": ScanDTO, "findings": [FindingDTO]}

# discovery/orchestrator.py
async def run_scan(db, tenant_id, domain) -> Scan:
    # passive -> active -> upsert -> findings -> status
```

`Asset` unique index: `UniqueConstraint(tenant_id, subdomain)` — the upsert key.

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | crt.sh parse/dedupe; DNS resolve; fingerprint extraction | Mock `httpx.AsyncClient`, `dns.resolver` per test |
| Integration | `POST /asm/scans` persists scan/assets/findings; re-scan upserts (no dupe); error→`error` status | SQLite via conftest `client`; mock external sources |
| Integration | `GET /asm/assets` isolation; `GET /asm/results/{scan_id}` cross-tenant 404 | Two tenants, app filter |
| E2E | 401 unauth; `lib/api.ts` fetch contract | ASGITransport (unauth); vitest fetch mock (client) |

## Threat Matrix

Applicable? The change **modifies application routing** (FastAPI `/asm` router, auth-gated) and performs credential-free external network calls, but exposes **no** shell-command, subprocess, VCS/PR-automation, or executable-file-classification boundary. All matrix rows below are `N/A`:

| Boundary | Applicability | Reason | Design response |
|---|---|---|---|
| Documentation-like paths | N/A | No `requirements.txt` execution; the dnspython pin is a passive manifest entry only | — |
| Git repository selection | N/A | No `git -C`/path authority logic | — |
| Commit state | N/A | VCS automation out of scope | — |
| Push state | N/A | VCS automation out of scope | — |
| PR commands | N/A | PR automation out of scope | — |

The external-network boundary is already governed by spec requirements: crt.sh called with no key, generous timeout, and source failure treated as partial (non-aborting). This maps directly to RED test `crt.sh unavailable` (spec scenario) and is carried into tasks.

## Migration / Rollout

Additive migration `003_attack_surface.py` (no existing-table changes, no data backfill). Rollback = drop the three new tables; removes no existing tenant/user data. Frontend rolls back by restoring prior static pages; `dnspython` pin is inert to revert. No feature flag needed.

## Open Questions

- [ ] Confirm `POST /asm/scans` body contract supersedes the scope header's `POST /asm/scan/{domain}` (resolved in favor of spec here).
