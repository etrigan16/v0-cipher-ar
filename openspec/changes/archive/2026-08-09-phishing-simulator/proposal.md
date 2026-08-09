# Proposal: Phishing Simulator (Sprint 3)

## Intent

Deliver the Phishing Simulator: tenants build templates and campaigns, generate per-target tracking links, and measure employee susceptibility (opens/clicks/reported/credentials). Today `/phishing` routes are stubs with no auth and no models. Delivery is links-only per the wiki consent model: Aukalabs never sends emails — the tenant distributes links internally.

## Scope

### In Scope
- Models: Template, Campaign, Target, Event (+ RLS, migration `005_phishing`, seeds)
- 8 seed templates (bank/government/tech) with `{{nombre}}`, `{{empresa}}`, `{{link}}` variables
- Structured editor: subject + HTML body + variables, preview with sample data, source toggle
- Campaign CRUD + CSV target upload + launch (unique per-target tokens) + cancel
- Public tracking: `GET /track/open/{token}.png`, `GET /track/click/{token}`, landing `GET|POST /l/{token}`
- Simulated credential capture: hash + discard, "credenciales" metric
- Results: aggregates + per-target table + PDF report
- Frontend: templates + editor, campaigns, results pages; extend `lib/api.ts`

### Out of Scope
- Real email sending (Resend) — links-only per wiki legal/consent model
- Subdomain landing (`[tenant].aukalabs.com`) — path-based `/l/{token}` for v1
- Drag-drop editor (dnd-kit) — structured editor v1, WYSIWYG v2
- Scheduled campaigns — no worker; `scheduled_at` stored, launch immediate

## Capabilities

### New Capabilities
- `phishing-templates`: Template model, tenant CRUD + preview, 8 seeds, variable rendering
- `phishing-campaigns`: Campaign/Target models, CRUD, CSV upload, launch/cancel, token generation
- `phishing-tracking`: Public `/track` + `/l/{token}` landing, Event log, token expiry, credential hash+discard
- `phishing-results`: Aggregation, per-target table, PDF report

### Modified Capabilities
- None (net-new; reuses `report-export` generator without spec change)

## Approach

Follow repo conventions: `get_current_user` tenant scoping (asm.py), `CoercingUuid` models, RLS loop in `init_db`, Alembic additive `005_phishing`, `lib/api.ts` client. Launch stages targets and generates unique tokens synchronously (bounded 100–2000 loop); landing renders template HTML with substituted variables; credentials POST stores only a SHA-256 hash. Tracking router is public but token-gated with 7-day expiry after `completed_at`. Effort estimate: ~2200–3000 lines.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/models/{template,campaign,target,event}.py` | New | 4 models + `__init__` registrations |
| `backend/app/routes/phishing.py` | Modified | Stubs → tenant-scoped CRUD/launch/results |
| `backend/app/routes/tracking.py` | New | Public `/track/*` + `/l/{token}` |
| `backend/app/database.py` | Modified | RLS loop for new tables |
| `backend/alembic/versions/005_phishing.py` | New | Tables + indexes + seed data |
| `backend/app/services/phishing/` | New | render, tracking, landing, results |
| `backend/app/main.py`, `config.py` | Modified | Router include, `tracking_base_url` |
| `backend/tests/test_phishing.py` | New | Full suite (waitlist mock style) |
| `lib/api.ts` | Modified | Extend phishing namespace |
| `app/dashboard/phishing/*` | Modified/New | Templates+editor, campaigns, results |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Legal/consent abuse | Med | Links-only; explicit tenant consent gate before launch |
| Token leakage (bearer landing creds) | Med | Unique tokens, 7-day expiry, Event audit log |
| Open tracking unreliable | High | De-emphasize open rate; clicks/credentials primary |
| Budget ~2200–3000 lines | High | Chained PRs (~6 slices); trim seeds if needed |

## Rollback Plan

DB: drop additive `005_phishing` revision. Routes: revert `phishing.py` stub, remove tracking router. Frontend: remove new pages. Feature-branch chain retargeting isolates each slice.

## Dependencies

- Existing: PostgreSQL RLS loop, Alembic chain, reportlab; no new packages

## Success Criteria

- [ ] `pytest backend`, `pnpm test`, `pnpm build` green
- [ ] Tenant A cannot read/write tenant B data
- [ ] Launch yields unique tokens; expired token → 410/404
- [ ] Credentials stored hash-only; results show open/click/report/credentials
- [ ] 8 templates render with substituted variables; preview works
