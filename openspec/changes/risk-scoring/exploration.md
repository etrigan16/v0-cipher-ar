# Exploration: risk-scoring — Risk Scoring + LLM Enrichment + Dashboard + Export (Sprint 2)

## Current State

Sprint 1 (`attack-surface-core`) is complete and archived (merged to `main` `c9c1071`). Live facts:

**Backend** (`backend/app/`):
- `models/finding.py` — `Finding`: `id`, `tenant_id` (FK), `asset_id` (FK), `scan_id` (FK), `severity` (`info|low|medium|high|critical`), `title`, `detail`, `discovered_at`. **No score, CVSS, remediation, enrichment, or status columns.**
- `models/asset.py` — `Asset`: `id`, `tenant_id`, `domain`, `subdomain`, `ip`, `port`, `service`, `fingerprint` (JSON text), `status`, `first_seen`, `last_seen`. **No `risk_score`** (the wiki's Sprint-1 sketch proposed one; it was not implemented).
- `models/scan.py` — `Scan`: `id`, `tenant_id`, `domain`, `status` (`pending|running|completed|error`), `started_at`, `completed_at`, `created_at`.
- **CRITICAL GAP**: `services/fingerprint.py::fingerprint()` never populates `FingerprintResult.findings` (the list is only initialized to `[]`; nothing appends to it; `to_dict()` omits it). `services/orchestrator.py::_process_subdomain` persists `Finding` rows only from `fr.findings`, which is always empty. **Real scans produce ZERO findings in production today** — the dashboard "Vulnerabilidades activas" card is always 0. Sprint 2 risk scoring has nothing to score until finding-generation rules exist.
- `routes/asm.py` — `POST /asm/scans`, `GET /asm/assets`, `GET /asm/stats`, `GET /asm/results/{scan_id}`. `FindingDTO` carries severity only. No findings-list, no risk summary, no asset detail, no export.
- `config.py` — `Settings`: `database_url`, `secret_key`, `resend_api_key`, DNS/HTTP/fingerprint knobs. **No LLM or export settings.**
- `requirements.txt` — no `openai`/`groq`/`anthropic`, no `reportlab`/`weasyprint`/`fpdf`. `httpx`, `dnspython`, `alembic` present.
- RLS: `database.py::init_db` enables RLS + `tenant_isolation` policy on `assets`, `scans`, `findings` (Postgres only); routes apply an app-level `tenant_id` filter (SQLite tests). New columns on `findings` inherit this — no new RLS work unless a new table is added.
- Migrations: `001_tenants`, `002_tenant_id_not_null`, `003_attack_surface`. Next is `004_*`.
- Tests: `tests/conftest.py` (SQLite + ASGITransport, env set pre-import), `tests/test_asm.py` (`_patch_discovery` monkeypatches orchestrator's crt.sh/DNS/fingerprint). 58 passed / 2 skipped at archive.

**Frontend**:
- `app/dashboard/page.tsx` — 4 stat cards (assets/findings/scans real from `/asm/stats`, phishing static 0) + empty-state CTA. No charts.
- `app/dashboard/attack-surface/page.tsx` — scan form + assets table (subdomain/IP/port/service/fingerprint title/status/first_seen). No findings view, no score column, no detail page.
- `lib/api.ts` — `api.asm.{listAssets, scanDomain, getResults, getStats}`; `Finding` type = id/asset_id/severity/title/detail/discovered_at.
- `package.json` — **`recharts` 2.15.0 is a dependency but imported nowhere** (greenfield for charts). No `@react-pdf/renderer`.
- Tests: vitest + RTL, `vi.stubGlobal("fetch", …)` + auth-context mock (`app/dashboard/page.test.tsx`).

**Product intent** (wiki, planning-level, repo code is truth):
- `plan-mvp.md` Sprint 3-4: "Risk scoring, LLM enrichment, Dashboard, Export PDF".
- `sprint-1-attack-surface.md` (Sprint 1-2 combined doc) weeks 3-4: RiskScoringEngine (CVSS base + exposure + context criticidad + tech debt; `score_tenant` → TenantRiskProfile); `Finding` sketch with `finding_type`, `cvss_score`, `description`, `remediation`, `resolved_at`; LLMEnricher (Groq: `summarize_findings`, `recommend_remediation`, `risk_context`; Redis cache TTL 24h, batch, fallback templates); Dashboard (AssetTable w/ score, RiskHeatmap, TenantSummary, Timeline; AssetDetail + FindingList); ReportGenerator (`executive_pdf`, `detailed_json`); ExportButton (PDF/JSON/CSV); aspirational `/api/v1/findings`, `PATCH /findings/{id}` (resolved/FP), `/api/v1/reports/executive`, `/api/v1/risk/profile`.
- `tech-decisions.md` ADR-005: **Groq (Llama-3.1-70b) primary + Ollama local fallback**; OpenAI too costly for bootstrap. ADR-002 (superseded) mentioned react-pdf/html2canvas under the old Vite stack.
- Pricing: Free plan includes "resumen PDF" — export is a monetized feature.

## Affected Areas

- `backend/app/models/finding.py` — add `risk_score` (Float), `risk_level` (String), `remediation` (Text), `context`/`llm_summary` (Text), `finding_type` (String), `status` (String, e.g. `open|resolved|fp`), `enriched_at` (DateTime) — all nullable/additive.
- `backend/app/models/asset.py` — add `risk_score` (Float) aggregate.
- `backend/alembic/versions/004_risk_scoring.py` — NEW additive migration.
- `backend/app/services/scoring/engine.py` — NEW deterministic risk engine (severity base + context factors).
- `backend/app/services/finding_rules.py` — NEW rule-based finding generator (fills the zero-findings gap).
- `backend/app/services/orchestrator.py` — run rules per fingerprint, persist findings, compute asset/finding scores post-scan.
- `backend/app/services/llm/enrich.py` — NEW optional LLM enrichment (OpenAI-compatible, Groq base URL; fallback templates when key absent).
- `backend/app/services/reports/generator.py` — NEW CSV + PDF (reportlab) executive report.
- `backend/app/routes/asm.py` — `GET /asm/findings`, `GET /asm/risk-summary`, `GET /asm/assets/{id}`, `GET /asm/export?format=csv|pdf`; extend DTOs.
- `backend/app/config.py` — optional `llm_api_key`, `llm_base_url`, `llm_model`, export settings.
- `backend/requirements.txt` — add `reportlab`; add OpenAI-compatible client (SDK or httpx-only, decision below).
- `backend/tests/test_scoring.py`, `test_finding_rules.py`, `test_llm_enrich.py`, `test_export.py` — NEW (mock LLM/report internals).
- `lib/api.ts` — extend asm types (Finding score fields, risk-summary, export) + new methods.
- `app/dashboard/findings/page.tsx` — NEW findings list with filters + risk score + remediation.
- `app/dashboard/assets/[id]/page.tsx` — NEW asset detail with findings (optional slice).
- `app/dashboard/page.tsx` — add risk distribution chart (recharts) + top findings.
- `app/dashboard/attack-surface/page.tsx` — risk score column on assets table.

## Approaches

### A. Risk score model
1. **Columns on `Finding` + aggregate on `Asset`** (recommended)
   - `Finding.risk_score` (Float 0–10) + derived `risk_level`; `Asset.risk_score` = max/weighted aggregate of its findings; tenant profile computed on the fly.
   - Pros: matches wiki sketch (`cvss_score` on Finding, `risk_score` on Asset); no new table → RLS already in place; additive nullable migration, trivial rollback; simple queries.
   - Cons: score history not preserved on re-score (overwrite semantics acceptable for MVP).
   - Effort: Low
2. **Separate `RiskScore`/`FindingStatus` tables**
   - Pros: full history/audit, per-finding factor breakdown.
   - Cons: new table → new RLS policy + migration + join complexity; overkill for MVP.
   - Effort: Medium

### B. Score computation
1. **Deterministic weighted formula (CVSS-like)** (recommended)
   - Base from severity (`info=0, low=2, medium=5, high=8, critical=10`) × context modifiers (exposed port/service, public-facing, TLS issues, outdated server header, missing security headers). Pure function of fingerprint+severity; fully unit-testable, no external calls.
   - Pros: deterministic, testable, zero external deps, explainable ("score = f(severity, context)").
   - Cons: not true CVSS; no CVE database integration (defer).
   - Effort: Low
2. **Real CVSS via CVE lookup (NVD API)**
   - Pros: industry-standard, accurate for known CVEs.
   - Cons: external API dependency, rate limits, key, latency; no CVE mapping exists in the pipeline today. Defer to v2.
   - Effort: High

### C. Finding generation (required pre-req)
1. **Rule-based `finding_rules.py` evaluated per fingerprint** (recommended)
   - Rules: missing HSTS, missing X-Content-Type-Options/CSP/security headers, TLS issues (expired/self-signed/mismatched CN), exposed non-standard ports, `Server` header version disclosure, cookie flags. Each rule emits `finding_type`, `severity`, `title`, `detail`, context factors for scoring.
   - Pros: fills the zero-findings gap so scoring/dashboard/export have real data; deterministic + testable; mirrors fingerprint service style (pure, injected deps).
   - Cons: scope addition beyond wiki's Sprint-2 prose (but required — Sprint 2 has nothing to score otherwise).
   - Effort: Medium
2. **Defer finding rules, score only existing findings**
   - Pros: smaller change.
   - Cons: production dashboards stay empty; Sprint 2 features are invisible without a real scan. Not viable.
   - Effort: Low (but ships a hollow feature)

### D. LLM enrichment
1. **OpenAI-compatible client via `openai` SDK pointed at Groq base URL, key OPTIONAL** (recommended)
   - `openai.AsyncOpenAI(base_url="https://api.groq.com/openai/v1", api_key=settings.llm_api_key)`; `GROQ_API_KEY`/`LLM_API_KEY` optional env var. When absent → enrichment skipped, deterministic fallback templates for `remediation`/`context`. Runs after scan (batch per scan) and/or `POST /asm/findings/{id}/enrich` on demand. Enrichment persisted on `Finding`; skip already-enriched findings (DB as cache — no Redis in infra today).
   - Pros: ADR-005 aligned (Groq); zero-cost MVP; degrades gracefully without a key; SDK handles retries/streaming; testable by mocking the client.
   - Cons: needs `openai` dep (~pure-python); LLM answers non-deterministic → tests assert shape not content.
   - Effort: Medium
2. **Raw httpx POST to OpenAI-compatible endpoint**
   - Pros: no new dependency.
   - Cons: reinvents retries/errors; more code; SDK is the standard path. Marginal gain.
   - Effort: Medium
3. **Ollama local fallback**
   - Pros: ADR-005 mentions it; fully offline.
   - Cons: not deployed anywhere; adds infra. Keep as future plug-in behind the same client interface (base_url swap), not implemented now.
   - Effort: High if done now; Medium to stub interface

### E. Export
1. **Backend CSV + PDF via `reportlab`** (recommended)
   - CSV via stdlib `csv`; PDF via reportlab (pure-Python, no system libs → works on `python:3.12-slim` Dockerfile without apt-get). `GET /asm/export?format=csv|pdf` returns tenant-scoped executive report (summary, severity distribution, top findings, remediation).
   - Pros: single backend path; free plan's "resumen PDF" monetization; pure-Python dep; testable (reportlab generates real bytes in tests).
   - Cons: reportlab layout code is imperative; fonts/layout minimal.
   - Effort: Medium
2. **Frontend PDF via `@react-pdf/renderer` / browser print**
   - Pros: no backend dep; styling in JSX.
   - Cons: new frontend dep, client-side rendering of large payloads, harder to test, auth/data already on backend.
   - Effort: Medium
3. **`weasyprint` (HTML→PDF)**
   - Pros: styled HTML output.
   - Cons: heavy system deps (pango/cairo) that break the slim Dockerfile; CI pain. Reject.
   - Effort: High

### F. API surface (additions to `/asm`)
- `GET /asm/findings` — list with `severity`/`asset_id`/`scan_id` filters, sort by `risk_score` desc, tenant-scoped.
- `GET /asm/risk-summary` — severity distribution counts, avg/max `risk_score`, top findings (drives dashboard charts).
- `GET /asm/assets/{asset_id}` — asset detail + its findings (drives AssetDetail page).
- `GET /asm/export?format=csv|pdf` — executive report, tenant-scoped.
- Optional: `POST /asm/findings/{id}/enrich` (on-demand LLM), `PATCH /asm/findings/{id}` (`status` → `resolved|fp`).
- `GET /asm/stats` extended with risk fields (backward compatible).

### G. Delivery / review budget
- Preflight: `review_budget_lines: 800`, `delivery_strategy: ask-on-risk`. Sprint 1 was ~1200–1600 lines across 4 chained PRs. Sprint 2 (rules + scoring + LLM + export + frontend) is comparable or larger → **chained PRs required**, forecast High budget risk.
- Suggested chain: PR 1 findings rules + scoring engine + migration; PR 2 API endpoints (findings/risk-summary/asset-detail/export CSV); PR 3 LLM enrichment; PR 4 PDF export + reportlab; PR 5 frontend (findings page, charts, api client). Optionally fold PDF into PR 2/4.

## Recommendation

**Combined approach**: 1A (score columns on `Finding` + aggregate `Asset.risk_score`, no new table) + 1B (deterministic CVSS-like weighted formula) + 1C rule-based finding rules as a **mandatory pre-req** (the pipeline currently produces zero findings) + 1D OpenAI-compatible client (Groq base URL, key optional, fallback templates, DB-persisted enrichment) + 1E backend CSV + reportlab PDF + 1F endpoint set, delivered as a **chained PR sequence** (4–5 slices) to respect the 800-line review budget. Defer: NVD/CVE lookup, Redis LLM cache, Ollama implementation, cloud provider APIs (already deferred).

Rationale: deterministic scoring is testable and explainable; optional-key LLM degrades gracefully and keeps CI green without secrets; reportlab fits the slim Docker image; additive nullable columns give trivial rollback; RLS/app-filter convention extends unchanged to all new endpoints (no new tables).

## Risks

- **Zero-findings gap**: if finding rules are dropped from scope, scoring/dashboard/export are hollow. Must be in scope.
- **LLM key absence**: without a key, enrichment is fallback templates only — feature is "ready but inert" until a key is set. Decision needed: ship inert or require key.
- **LLM non-determinism / cost**: batch enrichment, DB-persist, skip-already-enriched; tests mock the client and assert shape.
- **Review budget**: large change → chained PRs (forecast High). Must confirm slice order.
- **recharts**: dependency exists but unused — verify tree-shaking/SSR behavior in client components.
- **reportlab in Docker**: pure-python but must be pinned; verify import in slim image during CI.
- **Cross-tenant leaks**: every new endpoint must filter on `tenant_id` (app-level) — existing convention, enforce in tests.
- **Score drift on re-scan**: scores overwrite on re-scan; acceptable for MVP, document.

## Ready for Proposal

**Yes.** Scope: (1) rule-based finding generation, (2) deterministic risk scoring (finding + asset aggregate), (3) optional-key OpenAI-compatible LLM enrichment (Groq per ADR-005, fallback templates), (4) findings/risk-summary/asset-detail endpoints + CSV/PDF export, (5) dashboard risk charts + findings page, chained PR delivery.

Open decisions for the proposal round (ask-on-risk):
1. **LLM key**: is a Groq/OpenAI-compatible key available for this sprint, or ship enrichment with fallback templates only (key-added-later)? Provider confirm: Groq vs OpenAI directly.
2. **Finding rules in scope**: confirm the required scope addition (rules to generate findings — currently zero in prod).
3. **PATCH findings (resolved/FP)**: include in Sprint 2 or defer to hardening sprint?
4. **PDF approach**: backend reportlab (recommended) vs frontend @react-pdf/renderer vs browser print.
5. **Chained PR split**: confirm 5-slice chain (rules+scoring / API / LLM / PDF / frontend) vs fewer slices.
6. **Charts**: confirm MVP chart set (severity distribution bar + avg risk + top findings list) — no heatmap/timeline yet.
