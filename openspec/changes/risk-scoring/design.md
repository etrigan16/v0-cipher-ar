# Design: Risk Scoring, LLM Enrichment, Findings Dashboard & Export

## Technical Approach

Rule engine + deterministic scoring close the zero-findings gap: orchestrator runs pure rules per fingerprint, persists scored `Finding`s, recomputes `Asset.risk_score` (max of open findings), then batch-enriches via optional OpenAI-compatible Groq client (templates on failure). New tenant-scoped endpoints expose findings, risk summary, asset detail, PATCH, on-demand enrich, CSV/PDF export. Frontend: recharts dashboard + findings page with PATCH UI. 5 chained PRs (budget High).

## Architecture Decisions

| # | Decision | Options | Choice / Rationale |
|---|----------|---------|--------------------|
| D1 | Rules location | In `fingerprint.py` vs separate module | Separate `finding_rules.py` — pure, injectable, no-network tests; probe only gains header/cert capture |
| D2 | Scoring model | Full CVSS vs weighted base+modifiers | Weighted, clamp [0,10] — spec needs pure deterministic fn; no CVSS vector data |
| D3 | Asset aggregate | avg/sum vs max | `max(open findings)` — spec R3 |
| D4 | LLM client | Raw httpx vs `openai` SDK → Groq | OpenAI SDK (ADR-005); DB = cache (no Redis) |
| D5 | PDF | weasyprint/fpdf2 vs reportlab | reportlab — pure-Python, Docker-safe |
| D6 | Delivery | single PR vs chained | Chained ×5 — 800-line budget |

## Data Flow

    scan → fingerprint() → rules.evaluate() → Finding
      → scoring() → persist → recompute Asset.risk_score
      → enrich_scan_findings() (skips enriched; templates on failure)

## Scoring Formula

`score = clamp(base + Σ modifiers, 0, 10)`; `base[severity] = {info:0, low:2, medium:5, high:8, critical:10}`.

| Modifier | finding_type | Delta |
|---|---|---|
| exposed | `nonstandard-port` (port ∉ {80,443}) | +1.5 |
| tls_public | `tls-expired`, `tls-self-signed`, `tls-cn-mismatch` | +1.5 |
| version_leak | `server-version-disclosure` | +0.5 |
| header_missing | `missing-hsts`, `missing-csp`, `missing-xcto`, `insecure-cookie` | +0.5 |

Bands: `0→info, <4→low, <7→medium, <9→high, ≥9→critical`.

## Finding Rules

Pure `evaluate(fingerprint) -> list[RuleResult]`; deterministic, no I/O. `fingerprint.py` adds headers (`strict-transport-security`, `x-content-type-options`, `content-security-policy`, `set-cookie`) + cert fields (`not_before`, `not_after`, `issuer_cn`) to `to_dict()`.

| finding_type | Condition | severity |
|---|---|---|
| missing-hsts | https && no `strict-transport-security` | medium |
| missing-xcto | https && no `x-content-type-options` | low |
| missing-csp | https && no `content-security-policy` | medium |
| insecure-cookie | `set-cookie` lacks Secure or HttpOnly | medium |
| tls-expired | `tls.not_after < now` | high |
| tls-self-signed | `tls.issuer_cn == tls.subject_cn` | high |
| tls-cn-mismatch | hostname ∉ {subject_cn} ∪ SANs | high |
| nonstandard-port | port ∉ {None,80,443} | medium |
| server-version-disclosure | `server` matches `\d+\.\d+` | low |

## Migration 004

Additive, nullable: `findings` + `risk_score` Float, `risk_level`, `finding_type`, `remediation` Text, `context`/`llm_summary` Text, `enriched_at` DateTime, `status` NOT NULL default `open`. `assets` + `risk_score` Float. Downgrade drops only these; legacy rows NULL until next scan.

## LLM Enrichment

Config: `llm_api_key` (None → inert), `llm_base_url` (Groq), `llm_model`, `llm_timeout`. `enrich.py` builds `AsyncOpenAI` lazily when key set; prompt asks for JSON `{remediation, context}`; shape validated (both non-empty) else per-finding_type template. `enrich_scan_findings` batches post-scan, skips enriched, per-finding try/except (failure never aborts batch), sets `enriched_at` even on templates. On-demand `POST /asm/findings/{id}/enrich`, tenant-scoped 404.

## Endpoints

All queries filter `tenant_id`. DTOs: Finding + `risk_score, risk_level, finding_type, remediation, status, enriched_at`; Asset + `risk_score`. Aggregate = max of open findings' `risk_score`, NULL→0.0.

| Endpoint | Response |
|---|---|
| GET /asm/findings?severity&status&asset_id&scan_id&limit&offset | `{findings, total, limit, offset}`, `risk_score desc nullslast()` |
| GET /asm/risk-summary | `{severity_counts, avg_risk, max_risk, open_findings, top_findings[5]}`; empty → zeros |
| GET /asm/assets/{id} | `{asset, findings}`; cross-tenant/unknown → 404 |
| PATCH /asm/findings/{id} `{"status":"resolved"\|"fp"}` | updated finding; invalid → 422; then recompute aggregate |
| POST /asm/findings/{id}/enrich | updated finding; cross-tenant → 404 |
| GET /asm/export?format=csv\|pdf | bytes + Content-Disposition; bad format → 400 |
| GET /asm/stats | + `severity_counts`, `avg_risk`, `max_risk`, `open_findings` |

## Export

CSV: stdlib `csv`, headers `asset, finding title, severity, risk_score, status, remediation, discovered_at`, UTF-8; headers-only when empty. PDF: reportlab platypus in-memory — title, severity distribution, avg/max risk, top findings incl. remediation; empty → zeroed metrics. `text/csv`/`application/pdf` + `attachment`.

## Frontend

`lib/api.ts`: types + `listFindings, getRiskSummary, getAsset, patchFinding, enrichFinding, exportUrl`; stats risk fields. Dashboard: recharts severity distribution, avg/max cards, top findings (`components/dashboard/{severity-chart,top-findings,risk-cards}.tsx`). Findings page `app/dashboard/findings/page.tsx`: filterable table, severity badge, risk score, status, PATCH. Attack-surface: `risk_score` column + inline asset detail.

## Testing Strategy

| Layer | What | Approach |
|---|---|---|
| Unit | rules | fake fingerprints; fire/no-fire; determinism |
| Unit | scoring | base mapping, modifiers, clamp, bands, aggregate max, NULL→0.0 |
| Unit | LLM | mocked client: key absent→templates, failure→fallback, bad shape→fallback, enriched skipped |
| Unit | export | CSV headers/bytes/UTF-8; PDF `%PDF`; empty→headers-only/zeros |
| Integration | API | filters+sort, summary, asset 404, PATCH 422/404 + recompute, stats risk, cross-tenant isolation (`_patch_discovery`) |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.

## Rollout

Chained PRs, verifiable/revertable: PR1 rules+scoring+migration+orchestrator → PR2 API → PR3 LLM → PR4 export → PR5 frontend. Each keeps tests green. Rollback: per-slice revert; downgrade drops only added columns; LLM inert without `LLM_API_KEY`.

## Open Questions

None.
