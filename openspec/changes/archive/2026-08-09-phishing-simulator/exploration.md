# Exploration: phishing-simulator (Sprint 3)

## Current State

Backend is FastAPI 0.115 + SQLAlchemy 2.0 async + PostgreSQL 16 with established multi-tenant conventions:
- `backend/app/routes/phishing.py` is a stub: `GET /phishing/campaigns` → `{"campaigns": []}`, `POST /phishing/campaigns` → placeholder, `GET /phishing/campaigns/{id}/results` → zeros. **No auth dependency** (unlike `/asm` routes which use `get_current_user`).
- Tenant isolation pattern (see `routes/asm.py`): every query filters on `user.tenant_id` from `get_current_user` (app-level, works on SQLite); RLS policies are enabled per-table inside `database.py::init_db` (PostgreSQL only). New phishing tables must be added to the RLS loop + registered in `models/__init__.py` + imported in `init_db()`.
- Model conventions: `CoercingUuid` column type (duplicated per model file), `Base` from `app.database`, `tenant_id` FK → `tenants.id`, `Index("ix_*_tenant_id")`, `server_default=func.now()` timestamps.
- Migrations: Alembic, additive-first, revision IDs like `004_risk_scoring` (chained `down_revision`). A `005_phishing` migration is needed.
- Resend email pattern (`routes/waitlist.py`): raw `httpx` POST to `https://api.resend.com/emails` with `settings.resend_api_key`, fire-and-forget (never raises), from `onboarding@aukalabs.com`. Tests monkeypatch the send function (see `tests/test_waitlist.py`).
- Test harness: in-memory SQLite via `conftest.py`, `client` fixture with ASGITransport, `SECRET_KEY`/`RESEND_API_KEY` set before import.
- No Campaign/Template/Target/Event models exist. No task queue is wired (Redis is in the stack but not used for background jobs) — true time-based scheduling is not available without new infra.

Frontend: Next.js 16 + React 19 + TS strict + Tailwind 4 + shadcn/ui.
- `app/dashboard/phishing/page.tsx` is a static stub (disabled "Nueva campaña" button, hardcoded zeros).
- `lib/api.ts` has an `api.phishing` namespace hitting `/phishing/*` (campaigns/createCampaign/results). Frontend Resend usage exists in `app/api/send/route.ts` (resend SDK, not relevant to campaigns).
- Dashboard sidebar already links to `/dashboard/phishing`. No drag-drop dependency installed (no dnd-kit).

Wiki (gitignored — product source of truth) `sprint-3-phishing.md` specifies: 8 templates (Banco Nación, Galicia, Santander, BBVA, ARCA, MercadoLibre, Microsoft 365, Google), drag-drop editor with toolbar (texto, imagen, botón, spacer, divider) + variables sidebar (`{{nombre}}`, `{{empresa}}`, `{{email}}`, `{{enlace}}`, `{{fecha}}`) + HTML source toggle, campaign engine with CSV targets + scheduler, tracking pixel `/track/open/{token}.png` + redirect `/track/click/{token}`, landing pages on `[tenant].aukalabs.com/...`, results dashboard, PDF/CSV reports, and a security checklist (token expiry 7 days post-campaign, no real password storage — hash + discard, access log with IP + user-agent, tenant consent).

**Critical conflict found**: the wiki (both `sprint-3-phishing.md` and `gtm-pricing.md` legal section) explicitly states *"Aukalabs no envía emails; el tenant distribuye los links internamente"* — targets receive unique links, the tenant distributes them (e.g. via its own email/chat). The change brief instead says "send emails (Resend)" with a tracking pixel for opens. These are incompatible: a pixel only fires inside an HTML email; link distribution only enables click tracking.

## Affected Areas

- `backend/app/routes/phishing.py` — replace stubs with real tenant-scoped endpoints; add `get_current_user` (currently missing)
- `backend/app/models/` — new `template.py`, `campaign.py`, `target.py`, `event.py` (+ `__init__.py` registrations)
- `backend/app/database.py` — import new models; add phishing tables to the RLS loop
- `backend/alembic/versions/005_phishing.py` — new tables + indexes
- `backend/app/main.py` — include tracking router (public, token-based, outside `/phishing`)
- `backend/app/config.py` + `backend/.env.example` — `tracking_base_url` (absolute URLs for emails/pixel)
- `backend/app/services/` — new `phishing/` package: render (variable substitution), send (Resend), tracking, landing, results/analytics
- `backend/tests/` — new `test_phishing.py` (+ mock-Resend pattern from `test_waitlist.py`)
- `lib/api.ts` — extend phishing namespace (templates, campaigns, targets, results, tracking URL builders)
- `app/dashboard/phishing/page.tsx` — hub linking to templates/campaigns
- `app/dashboard/phishing/templates/page.tsx` (+ editor), `app/dashboard/phishing/campaigns/page.tsx`, `app/dashboard/phishing/campaigns/[id]/page.tsx` (results) — new pages
- `wiki/projects/aukalabs/sprint-3-phishing.md` — update status post-archive (gitignored, after apply)

## Approaches

### 1. Email delivery model (the core fork)
- **A. Send via Resend per target** (brief's assumption)
  - Pros: automated; open-tracking pixel works; matches "campaign engine" framing
  - Cons: contradicts wiki legal model ("Aukalabs no envía emails"); legal/abuse risk (sending phishing emails from our domain — Resend could flag the domain); needs verified sender + recipient consent handling; open rates unreliable (image blocking)
  - Effort: Medium
- **B. Generate unique tracking links; tenant distributes** (wiki source of truth)
  - Pros: legal-safe per gtm-pricing; no sender-domain risk; simpler send path (targets get CSV/link export); click + landing tracking fully works
  - Cons: open tracking useless (keep pixel only if tenant sends the provided HTML); less "automated wow"
  - Effort: Low-Medium
- **C. Hybrid**: build the send service (Resend) so each target gets a rendered HTML email with pixel + link, but make sending optional — launch exports per-target links/CSV; a `send_emails` step can be triggered when a tenant opts in
  - Pros: both worlds; open/click both available when used; default path stays legal
  - Cons: two code paths to test; scope creep
  - Effort: High

**Recommendation: C (hybrid), defaulting to B for launch** — implement the Resend send service because the brief requires it and it enables the pixel, but make launch produce distributable links by default so the wiki's legal stance holds. This is a proposal-round decision, not a design detail.

### 2. Tracking architecture
- **A. Single public `/track` router** — `GET /track/open/{token}.png` (1×1 transparent GIF, no-cache headers), `GET /track/click/{token}` (302 → landing URL), landing served at `GET /l/{token}` + `POST /l/{token}` (credentials, hashed-only). Token → target lookup, tenant-agnostic by design, expiry = 7 days after campaign `completed_at` (or last activity). Events appended to `Event` table (open/click/report/credentials + IP/UA metadata per wiki security log).
  - Pros: simple, no wildcard DNS, token-gated, works in dev (localhost)
  - Cons: not the `[tenant].aukalabs.com` subdomain branding from the wiki (deferrable to v2)
  - Effort: Medium
- **B. Dynamic subdomains** `[tenant].aukalabs.com/...` per wiki — requires wildcard DNS, TLS, whois opacity. Heavy infra, out of MVP reach.
  - Effort: High

**Recommendation: A**, with subdomains deferred and noted in the wiki as v2.

### 3. Template editor
- **A. Full drag-drop** (dnd-kit dep): real WYSIWYG blocks
  - Effort: High; new dependency; big test surface
- **B. Simplified structured editor** (no new dep): variable-aware fields (subject + HTML body with `{{variables}}`), preview pane rendering the HTML with sample variables, HTML source toggle, palette of 8 seed templates to fork. Matches the brief's own "(or simplified template editor)".
  - Effort: Medium

**Recommendation: B** for Sprint 3; drag-drop is the obvious v2 candidate (wiki already scopes editor as 3-4 days).

### 4. Target/event state model
- **A. Target columns + Event log** (recommended): canonical status columns on `Target` (`pending/sent/opened/clicked/reported`, `opened_at/clicked_at/...`) AND `Event` rows for audit (type, occurred_at, metadata{ip,user_agent}). Matches wiki model + satisfies "log de todos los accesos".
- **B. Events-only** (brief's Event model as sole source): leaner, but results aggregation and per-target status become derived queries.
- **Recommendation: A** — mirrors the wiki schema and existing `Asset`/`Finding` style.

### 5. Scheduling
No background worker exists. **Recommendation**: store `scheduled_at`; `launch` sends/stages immediately (synchronous per-target sends are fine at MVP scale — 100-2000 targets is a bounded loop; the waitlist already does fire-and-forget httpx). True cron/queue scheduling is deferred (Redis/Celery is a separate change).

## Recommended Structure (models)

- **Template**: id, tenant_id, name, category (`bank|government|tech`), subject, html_body (with `{{variables}}`), variables (JSON list), thumbnail (nullable), is_default (bool), created_at. Seed 8 templates (Alembic or startup seed).
- **Campaign**: id, tenant_id, name, template_id (FK), status (`draft|scheduled|running|completed|cancelled`), scheduled_at, started_at, completed_at, created_by (FK users), created_at.
- **Target**: id, tenant_id, campaign_id (FK), email, name, department, variables (JSON), tracking_token (unique, indexed), status (`pending|sent|opened|clicked|reported`), opened_at/clicked_at/reported_at, credentials_submitted_at.
- **Event**: id, tenant_id, campaign_id, target_id, type (`open|click|report|credentials`), occurred_at, metadata (JSON: ip, user_agent, etc.). Indexed by target_id + type.
- RLS: enable on all four tables (loop in `init_db`), tenant_id on each.

## Endpoints

All under existing `/phishing` prefix (keep — matches stub + `lib/api.ts`; note: wiki says `/api/v1/phishing` but the repo already standardized on `/phishing`), all auth-protected via `get_current_user`:

| Method | Path | Purpose |
|---|---|---|
| GET/POST | `/phishing/templates` | list / create |
| GET/PUT/DELETE | `/phishing/templates/{id}` | read / update / delete (tenant-scoped 404) |
| POST | `/phishing/templates/{id}/preview` | render with sample variables |
| GET/POST | `/phishing/campaigns` | list / create (name, template_id, targets: emails inline or CSV upload) |
| GET | `/phishing/campaigns/{id}` | detail + stats |
| POST | `/phishing/campaigns/{id}/launch` | stage targets, generate tokens, (optional) send emails, status→running→completed |
| POST | `/phishing/campaigns/{id}/cancel` | draft/scheduled → cancelled |
| GET | `/phishing/campaigns/{id}/results` | sent/opened/clicked/reported + per-target table |
| GET | `/phishing/campaigns/{id}/report` | PDF (reportlab, reuse `services/reports/generator.py`) |
| POST | `/phishing/targets/upload` | CSV → targets |
| GET | `/track/open/{token}.png` | **public** pixel, 1×1 GIF, no-cache |
| GET | `/track/click/{token}` | **public** 302 → landing |
| GET/POST | `/l/{token}` | **public** landing render / credentials submit (hash+discard) |

## Tests

- Backend (`tests/test_phishing.py`, follow `test_waitlist.py` monkeypatch style): template CRUD + tenant-scoped 404 + preview variable rendering; campaign create + CSV upload validation + launch (mocked send) generating unique tokens; tracking open/click updating target status + Event rows; token expiry (7-day) → 410/404; landing render + credentials submit storing only a hash; results aggregation; cross-tenant isolation.
- Frontend (vitest, fetch-stub pattern from `page.test.tsx`): templates grid, editor preview + variable insertion, campaigns list/create/launch, results table.

## Recommendation

Implement the brief's structure with the wiki as source of truth for product behavior: 4 models + migration 005 + RLS, `/phishing` CRUD + campaign engine + public `/track` + `/l` tracking/landing, results + PDF, frontend templates/campaigns/results pages, simplified editor. **Resolve the email-vs-links conflict via decision C (hybrid) before proposal** — this single decision shapes the send service, pixel, and results. Keep landing pages path-based (no subdomains), defer true scheduling and drag-drop.

## Risks

- **Legal/abuse (high)**: sending phishing emails from Aukalabs infrastructure conflicts with the wiki's consent model; Resend could flag the domain. Mitigate with hybrid model (links by default, send opt-in) + explicit tenant consent gate before launch.
- **Budget (high)**: largest change so far. Risk-scoring was 1400-1900 lines in 5 chained PRs; this change spans 4 models, ~12 endpoints, 8 seed templates (HTML-heavy), 3-4 frontend pages, tracking/landing. Forecast **~2200-3000 lines → High budget risk, chained PRs mandatory** (suggested 6 slices: models+migration+templates / campaign engine+send / tracking+landing / results+PDF / frontend templates+editor / frontend campaigns+results). Seed template HTML may push the count further — consider trimming to 3-4 polished templates + 4 basic if needed.
- **Open tracking reliability**: pixel-based opens are unreliable (image blocking); results should not over-index on open rate.
- **Token leakage**: unique tokens are bearer credentials for landing pages; enforce 7-day expiry + audit log per wiki.
- **Scheduling gap**: `scheduled_at` stored but no background worker; launch = immediate. Flag as explicit scope note.

## Ready for Proposal

**Yes** — exploration complete. Before `sdd-propose`, the user must decide:
1. **Email delivery**: send via Resend per target, links-only (wiki), or hybrid (recommended)?
2. **Landing pages**: path-based `/l/{token}` (recommended) vs subdomains (defer)?
3. **Credentials capture**: include simulated credential submission (hash+discard, adds the "credenciales" stat) or restrict Sprint 3 to open/click/report?
4. **Template editor**: simplified structured editor (recommended) vs full drag-drop?
5. **Delivery**: confirm chained PRs (~6 slices, High budget risk) for this change.
