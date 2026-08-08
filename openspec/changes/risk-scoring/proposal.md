# Proposal: Risk Scoring, LLM Enrichment, Findings Dashboard & Export (Sprint 2)

## Intent

Real scans emit **zero findings** today (`fingerprint()` never fills `FingerprintResult.findings`), so scoring/dashboard/export have nothing to show. Add rule-based finding generation (mandatory pre-req), deterministic CVSS-like scoring (finding + asset aggregate), optional-key LLM enrichment (Groq per ADR-005, template fallback), findings/risk-summary/asset-detail/export endpoints incl. PATCH status, and a recharts dashboard + findings page. Export PDF backs the monetized "resumen PDF" plan feature.

## Scope

### In Scope
- `finding_rules.py` rule engine (REQUIRED — pipeline produces no findings today)
- CVSS-like scoring engine + `Asset.risk_score` aggregate (additive migration 004)
- LLM enrichment: optional key, OpenAI-compatible Groq, DB-persisted, skip-enriched, template fallback
- Endpoints: `GET /asm/findings`, `GET /asm/risk-summary`, `GET /asm/assets/{id}`, `GET /asm/export?format=csv|pdf`, `PATCH /asm/findings/{id}` (resolved|fp); `/asm/stats` extended
- Backend CSV + reportlab PDF; frontend findings page, asset-detail, dashboard charts (recharts), score column

### Out of Scope
- NVD/CVE lookup, Redis cache, Ollama impl, finding-history tables, heatmap/timeline, cloud APIs

## Capabilities

### New Capabilities
- `risk-scoring`: rules + scoring engine + risk endpoints + findings page/charts
- `llm-enrichment`: optional-key Groq enrichment, template fallback, DB persistence
- `report-export`: backend CSV + reportlab PDF via `GET /asm/export`

### Modified Capabilities
- `attack-surface`: additive Finding/Asset score/remediation/status columns (migration 004); `/asm/stats` risk fields; zero-findings gap fixed

## Approach

Score columns on Finding + Asset aggregate (no new table → RLS/app-filter unchanged); deterministic weighted formula (severity base × context modifiers); rules per fingerprint (pure, injectable); `openai` SDK → Groq base URL, key optional (degrades to templates); reportlab (pure-python, slim Docker); all routes tenant-scoped. Delivered as **chained PRs** (budget High): rules+scoring / API / LLM / export+PDF / frontend.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `models/{finding,asset}.py`, `alembic/versions/004_*.py` | Mod/New | nullable score/remediation/status columns, `Asset.risk_score` |
| `services/{finding_rules,scoring/engine}.py` + `orchestrator.py` | New/Mod | rules, scoring, post-scan persistence |
| `services/{llm/enrich,reports/generator}.py` | New | LLM + CSV/PDF |
| `routes/asm.py`, `config.py`, `requirements.txt` | Mod | 5 endpoints, optional LLM settings, +openai/reportlab |
| `tests/test_{scoring,finding_rules,llm_enrich,export}.py` | New | unit tests (LLM mocked) |
| `lib/api.ts`, `app/dashboard/**` | Mod/New | types, pages, charts, score column |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| LLM key absent → inert feature | High | Optional key, fallback templates; ready-when-key-set |
| LLM non-determinism/cost | Med | Batch per scan, DB-persist, skip-enriched; assert shape |
| Budget > 800 lines | High | Chained PRs (5 slices) |
| Cross-tenant leak | Low | Tenant filter on every endpoint + isolation tests |

## Rollback Plan

Migration 004 additive/nullable → downgrade drops columns; no data rewrite. LLM off by unsetting env key. Chained PRs revert per-slice; frontend pages additive.

## Dependencies

- `reportlab` + `openai` SDK (pinned); `recharts` already present
- Optional env: `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`

## Success Criteria

- [ ] Real scan emits ≥1 finding; scoring deterministic
- [ ] All endpoints tenant-scoped; PATCH flips status; `pnpm test && cd backend && pytest` green
- [ ] CSV + PDF export produce valid bytes
- [ ] Dashboard charts + findings page render real data

## Proposal question round

Confirm: (1) MVP charts = severity distribution + avg/max risk + top findings (no heatmap/timeline)? (2) LLM batch post-scan only, or also on-demand enrich endpoint? (3) PATCH limited to `status` (resolved|fp)?
