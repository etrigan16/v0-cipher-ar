# Apply Progress — phishing-simulator (PR 6: Phase 6 Frontend + Phase 7 Verification)

- **Change**: phishing-simulator
- **Batch**: PR 6 of feature-branch-chain (`feature/phishing-simulator-p6` → previous PR branch `feature/phishing-simulator-p5` → tracker `feature/phishing-simulator`) — FINAL slice
- **Scope**: Phase 6 (Frontend: `lib/api.ts` + templates + campaigns + results pages + nav/hub) + Phase 7 (Verification: full suite + manual smoke)
- **Mode**: Strict TDD (openspec/config.yaml `apply.tdd: true`)
- **Artifact store**: hybrid
- **Date**: 2026-08-09
- **Commit range**: d17382c (PR5 HEAD) → PR6 HEAD (5 work-unit commits: 8e266b2, 35eaa73, 71fedc3, c19d69d, 7546172)

## Status — 28/28 tasks complete (Phases 1 + 2 + 3 + 4 + 5 + 6 + 7)

### Phase 1 (PR 1 — merged from previous batch)

| Task | Status |
|------|--------|
| 1.1 RED: `tests/test_migrations.py` 005 upgrade creates 4 tables + 8 seeds; downgrade drops cleanly | [x] |
| 1.2 Create `models/{template,campaign,target,event}.py` (CoercingUuid, `ix_*_tenant_id`, UQ campaign+email, unique nullable `tracking_token`, `server_default=func.now()`) | [x] |
| 1.3 Register all 4 in `models/__init__.py` | [x] |
| 1.4 Create `alembic/versions/005_phishing.py` (down_revision `004_risk_scoring`; FKs + indexes; 8 seeds tenant_id NULL: 3 bank/3 gov/2 tech, all with `{{nombre}}`,`{{empresa}}`,`{{link}}`) | [x] |
| 1.5 `database.py` `init_db`: RLS for templates/campaigns/targets/events; templates policy `tenant_id = current OR NULL` (D9) | [x] |
| 1.6 `config.py`: add `tracking_base_url` | [x] |

### Phase 2 (PR 2 — merged from previous batch)

| Task | Status |
|------|--------|
| 2.1 RED: template CRUD, cross-tenant 404, seed visibility, render escape/missing-var (templates R1–R4) | [x] |
| 2.2 `services/phishing/render.py`: 3-key `str.replace` + `html.escape` on target values, missing → empty (D7) | [x] |
| 2.3 `routes/phishing.py`: `GET/POST /templates`, `GET/PUT/DELETE /templates/{id}` with `get_current_user`; unknown/cross-tenant → 404 | [x] |

### Phase 3 (PR 3 — merged from previous batch)

| Task | Status |
|------|--------|
| 3.1 RED: campaign CRUD, CSV valid/invalid/dedupe, launch uniqueness + non-draft 409, cancel rules (campaigns R1–R6) | [x] |
| 3.2 `services/phishing/tokens.py`: `secrets.token_urlsafe(16)` generator (D1) | [x] |
| 3.3 `routes/phishing.py`: campaigns CRUD; target CSV upload (stdlib csv, validate in memory, one bulk insert, 422 + zero persisted — D6); `POST /campaigns/{id}/launch` (draft + ≥1 target, active + started_at, unique tokens + links); `POST /campaigns/{id}/cancel` (draft\|active → cancelled + completed_at) | [x] |

### Phase 4 (PR 4 — merged from previous batch)

| Task | Status |
|------|--------|
| 4.1 RED (threat matrix D5): `?url=https://evil` still 302 → `/l/{token}`; expired token → 410, no Event | [x] |
| 4.2 RED: open/click/landing/credential/report flows, 7-day expiry, IP/UA metadata, plaintext never stored (tracking R1–R6) | [x] |
| 4.3 `services/phishing/landing.py`: token→Target lookup, expiry rule (D2), Event recording with ip/user_agent | [x] |
| 4.4 Create `routes/tracking.py`: `/track/open/{token}.png` (1×1 PNG, no-store), `/track/click/{token}` (302 → `/l/{token}`), `GET /l/{token}` (render + notice + form), `POST /l/{token}/submit` (sha256 hash only → Event(credential), discard plaintext — D4), `POST /l/{token}/report` | [x] |
| 4.5 `main.py`: import + include tracking router | [x] |

### Phase 5 (PR 5 — merged from previous batch)

| Task | Status |
|------|--------|
| 5.1 RED: per-target results, summary zeroed (200), PDF `%PDF` magic + empty campaign (results R1–R3) | [x] |
| 5.2 `services/phishing/results.py`: per-target activity + aggregate counts/rates (open/click/credential) | [x] |
| 5.3 `services/reports/phishing_pdf.py` (PR-5 resolution of design D8): `ExportCampaignTarget` + `generate_campaign_pdf` reusing `_table_style` | [x] |
| 5.4 `routes/phishing.py`: `GET /campaigns/{id}/results`, `GET /results-summary`, `GET /campaigns/{id}/export?format=csv|pdf` | [x] |

### Phase 6 (PR 6 — this batch)

| Task | Status |
|------|--------|
| 6.1 RED UI: editor chip/preview/source toggle + results empty-state (vitest, `attack-surface` test pattern) | [x] |
| 6.2 `lib/api.ts`: `api.phishing.*` typed client (Template/Campaign/Target/Results types) | [x] |
| 6.3 `app/dashboard/phishing/templates/page.tsx`: list + structured editor (chips, live preview, source toggle — R5) | [x] |
| 6.4 `app/dashboard/phishing/campaigns/page.tsx`: campaigns hub — create, CSV upload, launch/cancel, link list | [x] |
| 6.5 `app/dashboard/phishing/results/page.tsx` + `results/[id]/page.tsx`: aggregate cards + per-target table + PDF download | [x] |

### Phase 7 (PR 6 — this batch)

| Task | Status |
|------|--------|
| 7.1 `pnpm test && cd backend && pytest` + `pnpm build` all green (115 FE / 288 BE + 2 skipped / build exit 0; `tsc --noEmit` clean; `pnpm lint` 0 errors) | [x] |
| 7.2 Manual smoke `pnpm dev`: hub/templates/campaigns/results 200; `results/[id]` dev 500 is a Turbopack dev-worker crash (env) — production build + vitest + tsc validate the route (launch-prompt resolution; isolation A-vs-B + 410-expiry covered by backend integration tests) | [x] |

**7/7 Phase 6+7 tasks complete.** **28/28 overall.** The phishing-simulator change is fully implemented and ready for verify.

## Work Unit Evidence (PR 6)

| Work unit | Focused test command + result | Runtime harness + result | Rollback boundary |
|-----------|-------------------------------|--------------------------|-------------------|
| 1. `lib/api.ts` phishing namespace | `pnpm vitest run lib/api.test.ts --pool=forks` → RED: 15 failed (functions absent, `api.phishing.*` stubs) → GREEN: **40 passed** (25 existing + 15 new: templates CRUD, campaigns CRUD, FormData upload, launch/cancel, results, summary, CSV/PDF export, error paths) | N/A — pure HTTP-client layer over mocked fetch; the real contract is exercised end-to-end by the backend integration suite (288 passed) + the page tests below that drive `api.phishing` against the same URL shapes | Revert 8e266b2 — `lib/api.ts` + `lib/api.test.ts` revert to the PR5 stubs; pages in later commits stop compiling (they import the new namespace) |
| 2. Templates page (list + structured editor) | `pnpm vitest run app/dashboard/phishing/templates/page.test.tsx --pool=forks` → RED: module not found → GREEN: **8 passed** (list/render, empty state, error, create→POST, delete→DELETE, chip insert at cursor, preview w/ sample values, source round-trip) | jsdom render + mocked fetch (URL-routing): real component tree, chips mutate the textarea value, preview substitutes sample values via `renderPreview` | Revert 35eaa73 — delete `templates/` dir; api namespace stays (additive) |
| 3. Campaigns page (list + create + CSV upload + launch/cancel) | `pnpm vitest run app/dashboard/phishing/campaigns/page.test.tsx --pool=forks` → RED: module not found → GREEN: **7 passed** (list/render, empty state, create→POST body, CSV upload→FormData, launch→POST + active + links shown, cancel→POST + cancelled, results link href) | jsdom render + mocked fetch: real file input change, FormData body assertion, launch link panel renders | Revert 71fedc3 — delete `campaigns/` dir |
| 4. Results pages (overview + per-campaign [id]) | `pnpm vitest run "app/dashboard/phishing/results" --pool=forks` → RED: modules not found → GREEN: **7 passed** (overview: summary cards `4 (40%)`, campaign links, empty state; [id]: table render, empty state, CSV export blob, PDF export blob) | jsdom render + mocked fetch + `URL.createObjectURL` stub; export buttons assert `/export?format=csv\|pdf` + createObjectURL called | Revert c19d69d — delete `results/` dir |
| 5. Nav links + hub page | `pnpm vitest run app/dashboard/layout.test.tsx app/dashboard/phishing/page.test.tsx --pool=forks` → RED: 2 failed (links absent) → GREEN: **4 passed** (layout keeps existing links + adds Plantillas/Campañas/Resultados hrefs; hub links to the three sub-pages) | jsdom render of `DashboardLayout` (auth-context + next mocks) and the hub page | Revert 7546172 — restore previous `layout.tsx` + `phishing/page.tsx` |

Full suite at PR6 HEAD: `pnpm test` → **115 passed / 16 files** (PR5 FE baseline 75 + 40 new, 0 regressions); `cd backend && python -m pytest -q` → **288 passed, 2 skipped** (unchanged, backend untouched); `pnpm build` → exit 0, 14 routes (incl. `/dashboard/phishing/results/[id]` ƒ dynamic).

## TDD Cycle Evidence (PR 6)

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 6.2 `lib/api.ts` phishing namespace | `lib/api.test.ts` | Unit (mocked fetch) | ✅ 75/75 FE (11 files, `--pool=forks`) | ✅ 15 failed (15 new tests; `api.phishing.listTemplates` etc. absent — only PR5 stubs `campaigns/createCampaign/results`) | ✅ 40 passed (after namespace + types + 204/FormData handling in `request`) | ✅ 15 cases (templates list/create/update/delete + error; campaigns list/create/upload(FormData+bearer)/launch(links)/cancel; results getCampaignResults/getResultsSummary/export CSV/PDF + error) | ✅ `request` gains 204-no-content + FormData-aware headers (no JSON Content-Type on multipart); `buildHeaders` keeps existing override semantics; stub namespace replaced, no callers existed |
| 6.3 Templates page (list + editor R5) | `app/dashboard/phishing/templates/page.test.tsx` | Integration (RTL + jsdom) | ✅ 75/75 FE | ✅ 8 failed (module not found) | ✅ 8 passed | ✅ 8 cases (list/render; empty; error; create→POST+refresh; delete→DELETE+removed; chip insert-at-cursor; preview w/ sample values; source toggle round-trip) | ✅ `renderPreview` + `PREVIEW_SAMPLE` + `TEMPLATE_VARIABLES` exported pure helpers (chips/vars/sample data as constants, testable without DOM) |
| 6.4 Campaigns page (list/create/upload/launch/cancel) | `app/dashboard/phishing/campaigns/page.test.tsx` | Integration (RTL + jsdom) | ✅ 75/75 FE | ✅ 7 failed (module not found) | ✅ 7 passed (after URL-routing mock fix — one-shot chains broke under `Promise.all` ordering) | ✅ 7 cases (list/render; empty; create body {name, template_id}; CSV upload→FormData; launch→active + links panel; cancel→cancelled; results link href) | ✅ URL-routing `mockImplementation` fixture; `uploadMsg` surfaces upload count (`N targets subidos`) for a real post-condition assert |
| 6.5 Results pages (overview + [id]) | `app/dashboard/phishing/results/page.test.tsx` + `[id]/page.test.tsx` | Integration (RTL + jsdom) | ✅ 75/75 FE | ✅ 7 failed (modules not found) | ✅ 7 passed | ✅ 7 cases (overview: summary cards `4 (40%)`/`2 (20%)`/credentials, campaign link href, empty state; [id]: table render (opened+clicked true), empty state, CSV export, PDF export) | ✅ `summarizeTargets` extracted as pure per-campaign aggregation (counts + rates over sent=active); export uses blob download (findings.tsx pattern); unused `refresh` callback removed after lint |
| 6.1+nav Layout/hub links | `app/dashboard/layout.test.tsx` + `app/dashboard/phishing/page.test.tsx` | Integration (RTL + jsdom) | ✅ 75/75 FE | ✅ 2 failed (Plantillas/Campañas/Resultados hrefs + hub links absent) | ✅ 4 passed | ✅ 4 cases (existing dashboard/attack-surface/phishing links preserved; 3 new phishing sub-links; hub links to templates/campaigns/results — multiple-match handled for the campaigns CTA) | ✅ Sidebar `sidebarLinks` extended; hub page rewritten from placeholder to link cards + CTA; `page.test.tsx` asserts hrefs only (no class assertions) |

### Test Summary (PR 6)
- **Total tests written**: 40 FE (15 api + 8 templates + 7 campaigns + 3 results overview + 4 results [id] + 1 hub + 2 layout — layout +2 includes the new sub-links test; 1 existing hub-count)
- **Total tests passing**: 40/40 in new/changed files; full FE suite 115 passed / 16 files (PR5 baseline 75 → +40, 0 regressions); backend unchanged 288 passed / 2 skipped
- **Layers used**: Unit (15, mocked fetch client), Integration (25, RTL + jsdom pages)
- **Approval tests**: None — no refactoring of existing production behavior (`request`/`buildHeaders` changes are additive: 204 + FormData handling; existing auth/asm/waitlist tests all still pass)
- **Pure functions created**: `renderPreview`, `PREVIEW_SAMPLE`, `TEMPLATE_VARIABLES`, `CATEGORY_LABELS`/`CATEGORY_OPTIONS` (templates page); `summarizeTargets` (results [id]); `STATUS_LABELS` (campaigns page)

## Files Changed (PR 6)

| File | Action | What Was Done |
|------|--------|---------------|
| `lib/api.ts` | Modified | `request()` now resolves 204 (DELETE) and skips JSON Content-Type for FormData; added `Template/TemplateInput/Campaign/CampaignInput/Target/LaunchedTarget/TargetResult/ResultsSummary` types; `api.phishing.*` namespace: listTemplates/createTemplate/updateTemplate/deleteTemplate, listCampaigns/getCampaign/createCampaign/listTargets/uploadTargets(FormData)/launchCampaign/cancelCampaign, getCampaignResults/getResultsSummary/exportCampaign(csv\|pdf → blob) |
| `lib/api.test.ts` | Modified | +15 cases: templates CRUD (incl. 204 + 404 error), campaigns CRUD (incl. FormData body + bearer), launch links, cancel, results, summary rates, CSV/PDF export blob + error |
| `app/dashboard/phishing/templates/page.tsx` | Created | List table (name/category/subject/created) + structured editor: name/category/subject/html_body fields, variable chips inserting `{{nombre}}/{{empresa}}/{{link}}` at cursor, live preview (sample values) vs source toggle (R5), create/update/delete via `api.phishing` |
| `app/dashboard/phishing/templates/page.test.tsx` | Created | 8 tests: list/render, empty, error, create, delete, chip insert, preview, source round-trip |
| `app/dashboard/phishing/campaigns/page.tsx` | Created | Campaign list (template name + target count) + create form (name + template select) + detail view: targets table, CSV file input → `uploadTargets`, launch (draft-only, shows distribution links), cancel (draft\|active), "Ver resultados" → `/dashboard/phishing/results/{id}` |
| `app/dashboard/phishing/campaigns/page.test.tsx` | Created | 7 tests: list/render, empty, create (body), CSV upload (FormData), launch (active + links), cancel, results link href |
| `app/dashboard/phishing/results/page.tsx` | Created | Overview: tenant aggregate cards (total/sent/opened+rate/clicked+rate/credentials) from `getResultsSummary` + campaign list each linking to per-campaign results |
| `app/dashboard/phishing/results/page.test.tsx` | Created | 3 tests: summary cards, campaign link href, empty state |
| `app/dashboard/phishing/results/[id]/page.tsx` | Created | Per-campaign: aggregate cards (client-side `summarizeTargets`) + per-target table (email/name/status/opened/clicked/credential) + Export CSV/PDF via blob download (`exportCampaign`) |
| `app/dashboard/phishing/results/[id]/page.test.tsx` | Created | 4 tests: table render, empty state, CSV export, PDF export |
| `app/dashboard/phishing/page.tsx` | Modified | Placeholder → hub landing with link cards to Plantillas/Campañas/Resultados + CTA (satisfies launch prompt task 5 "update phishing page to link to the new pages") |
| `app/dashboard/phishing/page.test.tsx` | Created | 1 test: hub links to the three sub-pages |
| `app/dashboard/layout.tsx` | Modified | Sidebar +3 links under Phishing: Plantillas (FileText), Campañas (Send), Resultados (BarChart3) |
| `app/dashboard/layout.test.tsx` | Modified | +1 test: asserts the 3 new hrefs while existing links keep passing |

## Deviations from Design / Launch Prompt / tasks.md

1. **Campaigns hub lives at `app/dashboard/phishing/campaigns/page.tsx`, NOT `app/dashboard/phishing/page.tsx`** (tasks.md 6.4 + design.md said `phishing/page.tsx`). The PR-6 launch prompt explicitly required `campaigns/page.tsx`; `phishing/page.tsx` became the hub landing page that links the three sections (also satisfying launch prompt task 5). tasks.md 6.4 wording updated with the resolution.
2. **Results split into `results/page.tsx` (overview) + `results/[id]/page.tsx` (per-campaign detail)** — launch prompt task 4 said "results/page.tsx (or campaign detail with results)" and tasks.md 6.5 said `results/[id]/page.tsx`; both are satisfied. The overview gives the tenant summary (backend `/results-summary`), the `[id]` page gives cards + per-target table + CSV/PDF export.
3. **Per-campaign aggregate cards are computed client-side** (`summarizeTargets` in `results/[id]/page.tsx`) because the backend's `/results-summary` is tenant-wide; the per-campaign endpoint returns raw per-target rows. Rates mirror the backend rule (denominator = `sent` i.e. active targets).
4. **Phase 7 task 7.2 redefined as manual smoke** (launch prompt task 8: `pnpm dev` pages load) instead of tasks.md's original "isolation E2E + 410 across tracking endpoints". The launch prompt is authoritative; the isolation/expiry scenarios remain covered by backend integration tests (`test_phishing_tracking.py` 11× 410 asserts; cross-tenant suites for campaigns/templates/results).
5. **Turbopack dev worker crash on `/dashboard/phishing/results/[id]`** (500 in `pnpm dev`) — an environment/compiler issue (log: "Jest worker encountered 2 child process exceptions" + OS `fork: Resource temporarily unavailable`), NOT an app error: `pnpm build` compiles all 14 routes (incl. the [id] route) with exit 0, vitest passes 4/4 on the page, and `tsc --noEmit` is clean. The other phishing pages return 200 in dev.

## Issues Found

- **Vitest default pool worker timeouts on this Windows box** (first `pnpm test` runs reported 4 files/37 tests with 7 infra errors). All runs with `--pool=forks` and the final plain `pnpm test` are clean (115/115). The canonical `pnpm test` passes; worker churn is a cold-start/resource artifact on this machine.
- **Campaigns test mocks**: one-shot `mockResolvedValueOnce` chains broke under `Promise.all` call ordering (listCampaigns+listTemplates fire concurrently); switched to URL-routing `mockImplementation` — more robust and closer to the real backend contract.
- `.atl/skill-registry*` files were already dirty before this batch (session noise, unrelated) — left uncommitted (same as PRs 3–5).

## Workload / PR Boundary

- Mode: chained PR slice (feature-branch-chain); PR 6 targets the previous PR branch `feature/phishing-simulator-p5` (tracker: `feature/phishing-simulator`). **This is the final slice of the chain.**
- Boundary: starts at d17382c (PR5 HEAD); ends with this batch's HEAD (5 work-unit commits: 8e266b2 api, 35eaa73 templates, 71fedc3 campaigns, c19d69d results, 7546172 nav/hub).
- Estimated review budget impact: **~2400 added / 60 deleted changed lines** — dominated by the four test files (~1,150 lines) and four page implementations (~1,100 lines). Reviewer-facing logic is the api namespace (~180 lines) + page components; the rest is RED UI tests required by 6.1 + the launch prompt's test task. The 800-line preflight budget is exceeded by design of this slice (whole frontend phase in one final PR); PR 5 already flagged the same pattern. If 800 is a hard gate, Phase 6 could be split into api+templates / campaigns / results+nav — the 5 work-unit commits are exactly those boundaries, so re-splitting into stacked PRs is mechanical.

### Status
28/28 tasks complete (6/6 P1 + 3/3 P2 + 3/3 P3 + 5/5 P4 + 4/4 P5 + 5/5 P6 + 2/2 P7). The phishing-simulator change is fully implemented. **Ready for sdd-verify** (then sdd-archive).
