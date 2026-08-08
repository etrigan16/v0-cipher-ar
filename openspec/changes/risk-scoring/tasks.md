# Tasks: Risk Scoring, LLM Enrichment, Dashboard & Export

Backend paths below relative to `backend/`; frontend to repo root.

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 1400–1900 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR1→PR2→PR3→PR4→PR5 |
| Delivery strategy | ask-on-risk |
| Chain strategy | feature-branch-chain |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

### Work Units

| PR | Goal | Focused test command | Runtime harness | Rollback |
|----|------|----------------------|-----------------|----------|
| 1 | rules+scoring+migration+orchestrator | `cd backend && pytest tests/test_finding_rules.py tests/test_scoring.py -q` | N/A pure modules; alembic up | revert; 004 drops cols |
| 2 | findings/risk-summary/asset/PATCH/stats | `cd backend && pytest tests/test_asm.py -q` | pytest httpx + `_patch_discovery` | revert; additive |
| 3 | LLM enrichment | `cd backend && pytest tests/test_llm_enrich.py -q` | N/A mocked client | revert; keyless→inert |
| 4 | CSV+PDF export | `cd backend && pytest tests/test_export.py -q` | assert `%PDF`/UTF-8 | revert; additive |
| 5 | frontend charts+pages+PATCH | `pnpm test && pnpm lint && tsc --noEmit` | `pnpm dev` manual | revert; additive |

## Phase 1: Foundation (PR1)

- [x] 1.1 `alembic/versions/004_risk_scoring.py`: add nullable `findings` cols `risk_score`, `risk_level`, `finding_type`, `remediation`, `context`, `llm_summary`, `enriched_at`, `status` default `open` + `assets.risk_score`; downgrade drops these
- [x] 1.2 Mirror cols in `app/models/finding.py`, `app/models/asset.py`
- [x] 1.3 `app/services/fingerprint.py`: capture `strict-transport-security`, `x-content-type-options`, `content-security-policy`, `set-cookie` → `to_dict()`
- [x] 1.4 `_extract_tls_from_cert()`: add `not_before`, `not_after`, `issuer_cn`
- [x] 1.5 RED: `tests/test_discovery.py` header/cert capture

## Phase 2: Rules + Scoring (PR1)

- [x] 2.1 Create `app/services/finding_rules.py`: pure `evaluate(fingerprint)` — 9 rules (hsts/xcto/csp missing, insecure-cookie, tls expired/self-signed/cn-mismatch, nonstandard-port, version-disclosure)
- [x] 2.2 RED: `tests/test_finding_rules.py` — fire/no-fire, determinism
- [x] 2.3 Create `app/services/scoring/engine.py`: pure `score(severity, fingerprint)` — base+modifiers, clamp [0,10], bands info/low/medium/high/critical
- [x] 2.4 RED: `tests/test_scoring.py` — base/modifiers/clamp/bands/max aggregate/NULL→0.0
- [x] 2.5 `app/services/orchestrator.py`: evaluate per fingerprint → persist Findings (`finding_type`, `risk_score`, `risk_level`); recompute `Asset.risk_score` = max open
- [x] 2.6 Extract `recompute_asset_risk(db, asset_id)` for scan + PATCH reuse

## Phase 3: API (PR2)

- [ ] 3.1 `app/routes/asm.py`: `GET /asm/findings` — filters severity/status/asset_id/scan_id, `risk_score desc nullslast()`, limit/offset
- [ ] 3.2 `GET /asm/risk-summary` — severity_counts, avg/max, open_findings, top 5; zeros when empty
- [ ] 3.3 `GET /asm/assets/{id}` — asset + findings; cross-tenant/unknown 404
- [ ] 3.4 `PATCH /asm/findings/{id}` (`resolved`|`fp`) — invalid 422, recompute aggregate
- [ ] 3.5 Extend `GET /asm/stats` risk fields
- [ ] 3.6 Extend `tests/test_asm.py`: filters/sort, summary, asset 404, PATCH 422/404+recompute, stats, cross-tenant

## Phase 4: LLM Enrichment (PR3)

- [ ] 4.1 `app/config.py` + `.env.example`: `llm_api_key`/`llm_base_url`/`llm_model`/`llm_timeout`
- [ ] 4.2 Create `app/services/llm/enrich.py`: lazy `AsyncOpenAI`, JSON `{remediation, context}`, shape validation, per-type templates
- [ ] 4.3 `enrich_scan_findings()`: post-scan batch, skip enriched, per-finding try/except, `enriched_at` on templates
- [ ] 4.4 `POST /asm/findings/{id}/enrich` — tenant 404
- [ ] 4.5 RED: `tests/test_llm_enrich.py` (mock): key absent→templates, failure→fallback, bad shape→fallback, enriched skipped

## Phase 5: Export (PR4)

- [ ] 5.1 Create `app/services/reports/generator.py`: `csv_report()` — stdlib, headers asset/title/severity/risk_score/status/remediation/discovered_at, headers-only when empty
- [ ] 5.2 `pdf_report()` — reportlab platypus, title/severity dist/avg-max/top findings+remediation, zeroed when empty
- [ ] 5.3 `GET /asm/export?format=csv|pdf` — Content-Type/Disposition; bad format 400
- [ ] 5.4 RED: `tests/test_export.py` — CSV headers/UTF-8, PDF `%PDF`, empty, tenant scoping
- [ ] 5.5 Pin `openai`, `reportlab` in `requirements.txt`

## Phase 6: Frontend (PR5)

- [ ] 6.1 `lib/api.ts`: extend Finding/Asset types (risk_score, risk_level, finding_type, remediation, status, enriched_at) + `listFindings`, `getRiskSummary`, `getAsset`, `patchFinding`, `enrichFinding`, `exportUrl`
- [ ] 6.2 Create `components/dashboard/severity-chart.tsx` (recharts), `risk-cards.tsx`, `top-findings.tsx`
- [ ] 6.3 Create `app/dashboard/findings/page.tsx`: filterable table, severity badge, risk score, status, PATCH UI
- [ ] 6.4 `app/dashboard/attack-surface/page.tsx`: `risk_score` column + inline asset detail
- [ ] 6.5 Wire `app/dashboard/page.tsx` charts/cards to risk-summary
- [ ] 6.6 Extend `lib/api.test.ts` + findings page vitest

## Phase 7: Verification

- [ ] 7.1 `pytest` (backend/) + `pnpm test && pnpm lint && tsc --noEmit` green
- [ ] 7.2 Manual smoke: scan→findings, export opens, PATCH flips status
