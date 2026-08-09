# Design: Phishing Simulator (Sprint 3)

## Technical Approach

Net-new tenant-scoped capability following repo conventions: `CoercingUuid` models + `ix_*_tenant_id`, additive Alembic `005_phishing`, RLS loop in `init_db`, `get_current_user` scoping, `lib/api.ts` client, shadcn pages. Public tracking router is token-gated (no auth), tenant-scoped via token→Target lookup. Links-only — no Resend calls.
## Architecture Decisions

| # | Decision | Alternatives | Rationale |
|---|----------|-------------|-----------|
| D1 | Token stored on `Target.tracking_token` (unique), `secrets.token_urlsafe(16)` at launch | HMAC-derived | Spec R3 needs unique indexed column; O(1) lookup, revocable |
| D2 | Expiry derived from campaign state: valid while `active`; `completed` → 7d past `completed_at`; else 410 | Expiry column | No sync bug; cancel stops immediately, completed keeps grace |
| D3 | Event.type `open\|click\|report\|credential\|landing` | Strict 4-type | Tracking R5 mandates landing audit |
| D4 | Credential: `sha256(f"{username}:{password}")` hex in Event.metadata, plaintext discarded | Plaintext (illegal); bcrypt (overkill) | Tracking R4: one-way hash proves capture |
| D5 | `/track/click` always 302 → `/l/{token}`; `?url=` in metadata only | Redirect to `?url=` | Public endpoint must not be an open redirector |
| D6 | CSV parsed with stdlib `csv`, validated in memory, then one bulk insert | Row-by-row insert | Malformed row → 422, zero persisted targets |
| D7 | Renderer: fixed 3-key `str.replace`; `html.escape` on target values; missing key → empty | Jinja2/string.Template | 3 fixed vars, no new dep, escape prevents injection |
| D8 | PDF via new `generate_campaign_pdf` in `services/reports/generator.py`, reusing `_table_style` | Separate module | Reuses reportlab stack; stays pure |
| D9 | Seeds `tenant_id IS NULL`; RLS `tenant_id = current OR NULL` | Copy seeds per tenant | Templates R3 "available to every tenant" |

## Data Flow

```
Tenant UI → /phishing/templates{/id} → Template (NULL tenant_id = seed)
Tenant UI → /phishing/campaigns{/id} → Campaign (draft)
POST /phishing/targets/upload (CSV) → Target (pending, no token)
POST /campaigns/{id}/launch → token_urlsafe(16)/target → active + started_at → [{token, landing_url}]
Public: /track/open/{t}.png → Event(open)+1×1 PNG | /track/click/{t}?url= → Event(click)+302 /l/{t}
        /l/{t} → render(template,{nombre,empresa,link})+form | /l/{t}/submit → sha256 → Event(credential)
        /l/{t}/report → Event(report)
Results: /campaigns/{id}/results | /results-summary | /campaigns/{id}/report (PDF)
```

## Model Schemas

```python
class Template(Base):  # templates
    id, tenant_id (FK, NULLABLE=seed), name, subject, html_body (Text),
    category (bank|government|tech), created_at   # ix_tenant_id
class Campaign(Base):  # campaigns
    id, tenant_id (FK), name, template_id (FK), status (draft|active|completed|cancelled),
    started_at, completed_at, created_at          # ix_tenant_id
class Target(Base):  # targets
    id, tenant_id (FK), campaign_id (FK), email, name, status (pending|active),
    tracking_token (String, unique, nullable), created_at
    # UQ (tenant_id, campaign_id, email); ix (campaign_id); ix (tracking_token) unique
class Event(Base):  # events
    id, tenant_id (FK), campaign_id (FK), target_id (FK), type,
    metadata (Text JSON: ip, user_agent, url, hash), occurred_at   # ix (campaign_id, type)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/models/{template,campaign,target,event}.py` | Create | 4 models |
| `backend/app/models/__init__.py` | Modify | Register models |
| `backend/alembic/versions/005_phishing.py` | Create | Tables + FKs + indexes + 8 seeds |
| `backend/app/database.py` | Modify | RLS loop; templates `OR NULL` |
| `backend/app/config.py` | Modify | `tracking_base_url` |
| `backend/app/routes/phishing.py` | Modify | Stubs → CRUD, upload, launch, cancel, results |
| `backend/app/routes/tracking.py` | Create | Public `/track/*` + `/l/{token}` |
| `backend/app/services/phishing/{render,tokens,landing,results}.py` | Create | Substitution, token gen, landing, aggregates |
| `backend/app/services/reports/generator.py` | Modify | `generate_campaign_pdf` + `ExportCampaignTarget` |
| `backend/app/main.py` | Modify | Include tracking router |
| `backend/tests/test_phishing.py` | Create | Full suite (asm style) |
| `lib/api.ts` | Modify | `api.phishing.*` typed client |
| `app/dashboard/phishing/page.tsx` | Modify | Campaigns hub (CSV upload, launch/cancel) |
| `app/dashboard/phishing/templates/page.tsx` | Create | List + editor (chips, preview, source) |
| `app/dashboard/phishing/results/[id]/page.tsx` | Create | Cards + table + PDF download |

## Interfaces / Contracts

Public tracking (no auth; unknown/expired → 404/410, no Event):
- `GET /track/open/{token}.png` → 1×1 PNG, no-store; records open
- `GET /track/click/{token}?url=` → records click, 302 → `/l/{token}` (D5)
- `GET /l/{token}` → 200 landing HTML; 410 expired
- `POST /l/{token}/submit` `{username,password}` → 200; sha256 → Event(credential)
- `POST /l/{token}/report` → Event(report)

Auth (`get_current_user`, cross-tenant → 404): templates CRUD; campaigns CRUD; `POST /targets/upload` (multipart CSV `email,name`, dedupe); `POST /campaigns/{id}/launch` (draft only, 409 otherwise, bounded 100–2000); `POST /campaigns/{id}/cancel` (draft|active); `GET /campaigns/{id}/results`; `GET /results-summary`; `GET /campaigns/{id}/report` → PDF.
## Testing Strategy

| Layer | What | Approach |
|-------|------|----------|
| Unit | render (escape/missing), CSV parse+dedupe, sha256, token gen, PDF | Pure functions, no mocks |
| Integration | CRUD scoping, cross-tenant 404, launch uniqueness, expiry 410 (−8d), no-plaintext, PDF magic | ASGITransport + SQLite (conftest), `_register_and_login` reuse |
| UI | Editor chip/preview/source; results empty state | Vitest + RTL (`attack-surface/page.test.tsx` pattern) |
| RED | `?url=https://evil` still 302 → `/l/{token}`; expired token records no Event | pytest first, then code |

## Threat Matrix

N/A — no shell/subprocess/VCS/PR automation. HTTP redirect boundary covered by D5 + RED test.

## Migration / Rollout

`005_phishing` (down_revision `004_risk_scoring`): 4 tables + FKs + unique indexes + 8 seeds (tenant_id NULL; 3 bank, 3 government, 2 tech; each with `{{nombre}}`, `{{empresa}}`, `{{link}}`). RLS loop appended in `init_db` (PostgreSQL-only; SQLite skips). Rollback: downgrade drops tables/seeds; revert `phishing.py` stub; remove tracking include; remove frontend pages.

Chained PR slices (~6, each <400 lines):
1. Models + migration + RLS + config — `pytest -k "model or migration"`; rollback: downgrade
2. Template CRUD + render + seeds — template tests
3. Campaign/Target CRUD + CSV + launch/cancel — campaign tests
4. Tracking router + landing + hashing — tracking tests (RED open-redirect)
5. Results + `generate_campaign_pdf` — results/PDF tests
6. Frontend: `lib/api.ts` + templates/editor + campaigns + results — `pnpm test && pnpm build`

## Open Questions

- [ ] Event.type includes `landing` (tracking R5 vs R6)? Default: yes
- [ ] `tracking_base_url` default vs env-only in prod (Caddy `api.aukalabs.com`)?
