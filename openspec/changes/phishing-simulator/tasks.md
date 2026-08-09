# Tasks: Phishing Simulator (Sprint 3)

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 2200–3000 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 → PR 2 → PR 3 → PR 4 → PR 5 → PR 6 |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending (proposal rollback hints feature-branch-chain) |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Models + migration 005 + RLS + config | PR 1 | `cd backend && pytest -k "migration"` | `docker compose up db` + `alembic upgrade head` (RLS needs PG) | `alembic downgrade 004` |
| 2 | Template CRUD + render + seeds | PR 2 | `cd backend && pytest -k "template or render"` | pytest ASGITransport (SQLite conftest) | drop template routes/render; table additive |
| 3 | Campaign/Target CRUD + CSV + launch/cancel | PR 3 | `cd backend && pytest -k "campaign or target or csv or launch"` | pytest ASGITransport | drop campaign routes; tables additive |
| 4 | Tracking + landing + hashing | PR 4 | `cd backend && pytest -k "tracking or landing or credential or expiry"` | pytest; `uvicorn app.main:app` + curl token flow | remove tracking router + include |
| 5 | Results + PDF export | PR 5 | `cd backend && pytest -k "results or summary or pdf"` | pytest (`%PDF` magic assert) | drop results routes + generator fn |
| 6 | Frontend api.ts + pages | PR 6 | `pnpm test && pnpm build` | `pnpm dev` browser flow | revert api.ts + delete pages |

## Phase 1: Foundation — Models, Migration, RLS (PR 1)

- [x] 1.1 RED: `tests/test_migrations.py` 005 upgrade creates 4 tables + 8 seeds; downgrade drops cleanly
- [x] 1.2 Create `models/{template,campaign,target,event}.py` (CoercingUuid, `ix_*_tenant_id`, UQ campaign+email, unique nullable `tracking_token`, `server_default=func.now()`)
- [x] 1.3 Register all 4 in `models/__init__.py`
- [x] 1.4 Create `alembic/versions/005_phishing.py` (down_revision `004_risk_scoring`; FKs + indexes; 8 seeds tenant_id NULL: 3 bank/3 gov/2 tech, all with `{{nombre}}`,`{{empresa}}`,`{{link}}`)
- [x] 1.5 `database.py` `init_db`: RLS for templates/campaigns/targets/events; templates policy `tenant_id = current OR NULL` (D9)
- [x] 1.6 `config.py`: add `tracking_base_url`

## Phase 2: Template CRUD + Renderer (PR 2)

- [ ] 2.1 RED: template CRUD, cross-tenant 404, seed visibility, render escape/missing-var (templates R1–R4)
- [ ] 2.2 `services/phishing/render.py`: 3-key `str.replace` + `html.escape` on target values, missing → empty (D7)
- [ ] 2.3 `routes/phishing.py`: `GET/POST /templates`, `GET/PUT/DELETE /templates/{id}` with `get_current_user`; unknown/cross-tenant → 404

## Phase 3: Campaign CRUD + CSV + Launch/Cancel (PR 3)

- [ ] 3.1 RED: campaign CRUD, CSV valid/invalid/dedupe, launch uniqueness + non-draft 409, cancel rules (campaigns R1–R6)
- [ ] 3.2 `services/phishing/tokens.py`: `secrets.token_urlsafe(16)` generator (D1)
- [ ] 3.3 `routes/phishing.py`: campaigns CRUD; `POST /targets/upload` (stdlib csv, validate in memory, one bulk insert, 422 + zero persisted — D6); `POST /campaigns/{id}/launch` (draft only, 100–2000 bounded, active + started_at, return links); `POST /campaigns/{id}/cancel` (draft|active → cancelled + completed_at)

## Phase 4: Public Tracking + Landing (PR 4)

- [ ] 4.1 RED (threat matrix D5): `?url=https://evil` still 302 → `/l/{token}`; expired token → 410, no Event
- [ ] 4.2 RED: open/click/landing/credential/report flows, 7-day expiry, IP/UA metadata, plaintext never stored (tracking R1–R6)
- [ ] 4.3 `services/phishing/landing.py`: token→Target lookup, expiry rule (D2), Event recording with ip/user_agent
- [ ] 4.4 Create `routes/tracking.py`: `/track/open/{token}.png` (1×1 PNG, no-store), `/track/click/{token}` (302 → `/l/{token}`), `GET /l/{token}` (render + notice + form), `POST /l/{token}/submit` (sha256 hash only → Event(credential), discard plaintext — D4), `POST /l/{token}/report`
- [ ] 4.5 `main.py`: import + include tracking router

## Phase 5: Results + PDF (PR 5)

- [ ] 5.1 RED: per-target results, summary zeroed (200), PDF `%PDF` magic + empty campaign (results R1–R3)
- [ ] 5.2 `services/phishing/results.py`: per-target activity + aggregate counts/rates (open/click/credential)
- [ ] 5.3 `services/reports/generator.py`: `ExportCampaignTarget` + `generate_campaign_pdf` reusing `_table_style` (D8)
- [ ] 5.4 `routes/phishing.py`: `GET /campaigns/{id}/results`, `GET /results-summary`, `GET /campaigns/{id}/report`

## Phase 6: Frontend (PR 6)

- [ ] 6.1 RED UI: editor chip/preview/source toggle + results empty-state (vitest, `attack-surface` test pattern)
- [ ] 6.2 `lib/api.ts`: `api.phishing.*` typed client (Template/Campaign/Target/Results types)
- [ ] 6.3 `app/dashboard/phishing/templates/page.tsx`: list + structured editor (chips, live preview, source toggle — R5)
- [ ] 6.4 `app/dashboard/phishing/page.tsx`: campaigns hub — create, CSV upload, launch/cancel, link list
- [ ] 6.5 `app/dashboard/phishing/results/[id]/page.tsx`: aggregate cards + per-target table + PDF download

## Phase 7: Verification

- [ ] 7.1 `pnpm test && cd backend && pytest` + `pnpm build` all green
- [ ] 7.2 Isolation end-to-end (tenant A vs B) + expired-token 410 across all tracking endpoints
