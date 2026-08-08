```yaml
schema: gentle-ai.verify-result/v1
evidence_revision: sha256:cc88ed56ca250d8422612cdd6a959c82a050936c328022651751af3587d70aea
verdict: pass
blockers: 0
critical_findings: 0
requirements: 19/19
scenarios: 46/46
test_command: pnpm test && cd backend && pytest -q
test_exit_code: 0
test_output_hash: sha256:665be1bbc700047a3eafa4cdb1c69ce47ddcc35badcf19207173a86d2be02582
build_command: pnpm build
build_exit_code: 0
build_output_hash: sha256:98a4d6e7e47bc9411e2b97494fa06fafea4e2d27553d0cf35df132889cc8f257
```

# Verification Report

**Change**: risk-scoring
**Version**: N/A (delta specs)
**Mode**: Strict TDD (openspec/config.yaml `apply.tdd: true`)

## Completeness

| Metric | Value |
|--------|-------|
| Tasks total | 29 |
| Tasks complete | 29 |
| Tasks incomplete | 0 |

All 29 tasks across 5 PR slices marked `[x]` in `tasks.md` and confirmed in `apply-progress.md` (11/11 PR1, 6/6 PR2, 5/5 PR3, 5/5 PR4, 8/8 PR5). Change merged to `main` at cd8d09c; working tree clean (only skill-registry cache files modified, unrelated).

## Build & Tests Execution

**Build**: ✅ Passed
```text
pnpm build — exit 0 (hash sha256:98a4d6e7...)
Static routes: /dashboard, /dashboard/attack-surface, /dashboard/findings, /dashboard/mfa, /dashboard/phishing, /login, /register
```

**Tests**: ✅ 75 frontend passed + 165 backend passed / 2 skipped
```text
pnpm test && cd backend && pytest -q — exit 0 (hash sha256:665be1bb...)
  vitest: Test Files 11 passed (11), Tests 75 passed (75)
  pytest: 165 passed, 2 skipped, 4 warnings in 43.51s
```

**Type check**: `npx tsc --noEmit` — exit 0, zero diagnostics (hash sha256:e3b0c44..., empty output).

**Lint**: `pnpm lint` — exit 0, 0 errors / 7 warnings (pre-existing, `hooks/use-mobile.ts` set-state-in-effect, etc. — not introduced by this change).

**Coverage**: ➖ Not available (no coverage threshold configured; `coverage_threshold: 0`).

## Spec Compliance Matrix

### risk-scoring (7 requirements, 19 scenarios)

| Requirement | Scenario | Test | Result |
|-------------|----------|------|--------|
| R1 Finding Generation Rules | Rule fires on fingerprint | `test_finding_rules.py::TestRules::test_hsts_missing_fires_medium` et al. (22 rule tests) | ✅ COMPLIANT |
| R1 | No rule matches | `test_finding_rules.py::test_clean_fingerprint_produces_no_findings` | ✅ COMPLIANT |
| R1 | Deterministic rules | `test_finding_rules.py::test_deterministic_output` | ✅ COMPLIANT |
| R2 Finding Score Computation | Critical exposed service scores high | `test_scoring.py::TestClamping::test_critical_exposed_clamped_to_10` + `TestModifiers::test_exposed_nonstandard_port_adds_1_5` | ✅ COMPLIANT |
| R2 | Deterministic output | `test_scoring.py::TestDeterminism::test_deterministic_output` | ✅ COMPLIANT |
| R2 | Clamping | `test_scoring.py::TestClamping::test_clamp_never_exceeds_10` | ✅ COMPLIANT |
| R3 Asset Risk Aggregate | Asset with findings | `test_scoring.py::TestAggregate::test_max_of_open_findings` + `test_asm.py::test_recompute_asset_risk_max_of_open_findings` | ✅ COMPLIANT |
| R3 | Asset without findings | `test_scoring.py::TestAggregate::test_empty_and_all_null_yield_zero` + `test_asm.py::test_recompute_asset_risk_zero_without_open` | ✅ COMPLIANT |
| R3 | Re-scan overwrites | `test_asm.py::test_rescan_overwrites_prior_findings` | ✅ COMPLIANT |
| R4 Findings List Endpoint | Tenant lists findings | `test_asm.py::TestFindingsList::test_lists_findings_sorted_by_risk_desc` | ✅ COMPLIANT |
| R4 | Filter by status | `test_asm.py::TestFindingsList::test_filters_by_status` | ✅ COMPLIANT |
| R4 | Cross-tenant isolation | `test_asm.py::TestFindingsList::test_cross_tenant_findings_hidden` | ✅ COMPLIANT |
| R5 Risk Summary Endpoint | Summary from real data | `test_asm.py::TestRiskSummary::test_summary_reflects_only_own_tenant` | ✅ COMPLIANT |
| R5 | Empty tenant | `test_asm.py::TestRiskSummary::test_empty_tenant_returns_zeros` | ✅ COMPLIANT |
| R6 Asset Detail Endpoint | Asset with findings | `test_asm.py::TestAssetDetail::test_asset_with_findings` | ✅ COMPLIANT |
| R6 | Cross-tenant or unknown asset | `test_asm.py::TestAssetDetail::test_cross_tenant_asset_404` + `test_unknown_asset_404` | ✅ COMPLIANT |
| R7 Finding Status Update | Resolve a finding | `test_asm.py::TestFindingPatch::test_resolve_recomputes_asset_risk` | ✅ COMPLIANT |
| R7 | Invalid status rejected | `test_asm.py::TestFindingPatch::test_invalid_status_422` | ✅ COMPLIANT |
| R7 | Cross-tenant PATCH denied | `test_asm.py::TestFindingPatch::test_cross_tenant_patch_404` | ✅ COMPLIANT |

### llm-enrichment (4 requirements, 10 scenarios)

| Requirement | Scenario | Test | Result |
|-------------|----------|------|--------|
| R1 Optional Key with Template Fallback | Key configured | `test_config.py::test_llm_overrides_read_from_environment` + `test_llm_enrich.py::TestLLMSuccess::test_llm_payload_parsed_and_shape_validated` | ✅ COMPLIANT |
| R1 | Key absent | `test_config.py::test_llm_defaults_when_key_absent` + `test_llm_enrich.py::TestTemplateFallback::test_key_absent_uses_template_and_keeps_rule_remediation` | ✅ COMPLIANT |
| R1 | LLM call failure | `test_llm_enrich.py::TestLLMSuccess::test_llm_failure_falls_back_to_template` | ✅ COMPLIANT |
| R2 Enrichment Batch and On-Demand | Batch after scan | `test_llm_enrich.py::TestBatchEnrichment::test_batch_enriches_all_findings_with_templates` + `test_orchestrator_run_scan_enriches_findings` | ✅ COMPLIANT |
| R2 | On-demand enrich | `test_llm_enrich.py::TestOnDemandEnrichEndpoint::test_on_demand_enrich_success` | ✅ COMPLIANT |
| R2 | Cross-tenant enrich denied | `test_llm_enrich.py::TestOnDemandEnrichEndpoint::test_on_demand_cross_tenant_404` | ✅ COMPLIANT |
| R3 Persistence | Enriched fields stored | `test_llm_enrich.py::TestBatchEnrichment::test_batch_enriches_all_findings_with_templates` (reads back populated rows) | ✅ COMPLIANT |
| R4 Non-determinism Handling | Already-enriched skipped | `test_llm_enrich.py::TestBatchEnrichment::test_batch_skips_already_enriched` | ✅ COMPLIANT |
| R4 | Shape validation | `test_llm_enrich.py::TestLLMSuccess::test_bad_shape_falls_back_to_template` (4 bad-shape cases) | ✅ COMPLIANT |
| R4 | Deterministic tests | `test_llm_enrich.py` (all tests use mocked `AsyncOpenAI` client, assert shape/flow) | ✅ COMPLIANT |

### report-export (4 requirements, 8 scenarios)

| Requirement | Scenario | Test | Result |
|-------------|----------|------|--------|
| R1 CSV Export | CSV from tenant findings | `test_export.py::TestCsvGenerator::test_headers_match_spec` + `test_one_row_per_finding_with_values` + `test_utf8_round_trips` | ✅ COMPLIANT |
| R1 | Empty tenant | `test_export.py::TestCsvGenerator::test_headers_match_spec` (headers-only) | ✅ COMPLIANT |
| R2 PDF Export | PDF with real data | `test_export.py::TestPdfGenerator::test_pdf_with_findings` (`%PDF` + summary/distribution/top) | ✅ COMPLIANT |
| R2 | Empty tenant | `test_export.py::TestPdfGenerator::test_pdf_empty_tenant_zeroed_metrics` | ✅ COMPLIANT |
| R3 Export Endpoint | CSV download | `test_export.py::TestExportEndpoint::test_csv_download` (text/csv + attachment) | ✅ COMPLIANT |
| R3 | PDF download | `test_export.py::TestExportEndpoint::test_pdf_download` (application/pdf + attachment) | ✅ COMPLIANT |
| R3 | Invalid format | `test_export.py::TestExportEndpoint::test_invalid_format_400` + `test_missing_format_400` | ✅ COMPLIANT |
| R4 Tenant Scoping | Tenant-scoped content | `test_export.py::TestExportEndpoint::test_tenant_scoped_content` | ✅ COMPLIANT |

### attack-surface (delta: 4 requirements, 9 scenarios)

| Requirement | Scenario | Test | Result |
|-------------|----------|------|--------|
| Finding Model (MODIFIED) | Finding linked to asset and scan | `test_asm.py::test_finding_links_asset_and_scan` | ✅ COMPLIANT |
| Finding Model | New columns default safely | `test_asm.py::test_new_columns_default_safely` | ✅ COMPLIANT |
| Asset Model (MODIFIED) | Asset created for discovered host | `test_asm.py::test_asset_persists_all_fields` + `test_discovery.py::test_full_fingerprint_dict` | ✅ COMPLIANT |
| Asset Model | Re-scan upserts instead of duplicating | `test_asm.py::test_rescan_upsert_no_duplicate` + `test_rescan_no_duplicate_and_preserves_first_seen` | ✅ COMPLIANT |
| Asset Model | risk_score nullable on legacy rows | `test_asm.py::test_risk_score_nullable_then_settable` | ✅ COMPLIANT |
| Migration 004 (ADDED) | Upgrade on existing data | `test_migrations.py::test_004_upgrade_adds_columns_and_preserves_rows` | ✅ COMPLIANT |
| Migration 004 | Downgrade | `test_migrations.py::test_004_downgrade_drops_only_added_columns` | ✅ COMPLIANT |
| Stats Risk Fields (ADDED) | Stats include risk fields | `test_asm.py::test_stats_risk_fields_reflect_richer_data` | ✅ COMPLIANT |
| Stats Risk Fields | Backward compatible | `test_asm.py::test_stats_counts_only_own_tenant` (legacy shape preserved) | ✅ COMPLIANT |

**Compliance summary**: 46/46 scenarios compliant (19/19 requirements).

## Correctness (Static Evidence)

| Requirement | Status | Notes |
|------------|--------|-------|
| R1 rules module | ✅ Implemented | `app/services/finding_rules.py` — 9 pure rules, injectable `now`, RuleResult with remediation |
| R2 scoring engine | ✅ Implemented | `app/services/scoring/engine.py` — base+modifiers, clamp [0,10], bands info/low/medium/high/critical |
| R3 aggregate | ✅ Implemented | `recompute_asset_risk` = max of open findings, NULL→0.0, reused by scan + PATCH |
| R4 findings list | ✅ Implemented | `GET /asm/findings` — filters severity/status/asset_id/scan_id, `risk_score desc nullslast()`, limit/offset |
| R5 risk summary | ✅ Implemented | `GET /asm/risk-summary` — severity_counts/avg/max/open_findings/top 5; zeros when empty |
| R6 asset detail | ✅ Implemented | `GET /asm/assets/{id}` — 404 cross-tenant/unknown/malformed (via `_coerce_uuid`) |
| R7 PATCH status | ✅ Implemented | `PATCH /asm/findings/{id}` — Literal `open|resolved|fp`, 422 invalid, recompute aggregate |
| LLM R1-R4 | ✅ Implemented | `app/services/llm/enrich.py` — lazy AsyncOpenAI, templates, shape validation, skip-enriched, batch + on-demand |
| Export R1-R4 | ✅ Implemented | `app/services/reports/generator.py` + `GET /asm/export` — stdlib CSV, reportlab PDF, Content-Type/Disposition, 400/401 |
| Migration 004 | ✅ Implemented | `alembic/versions/004_risk_scoring.py` — additive nullable columns; downgrade drops only those |
| Stats risk fields | ✅ Implemented | `GET /asm/stats` extended with severity_counts/avg/max/open_findings, legacy counts unchanged |
| Frontend | ✅ Implemented | `lib/api.ts` endpoints, `risk-distribution.tsx` chart, findings page with PATCH/enrich/export, dashboard risk section, attack-surface risk column |

## Coherence (Design)

| Decision | Followed? | Notes |
|----------|-----------|-------|
| D1 Rules in separate module | ✅ Yes | `finding_rules.py`, pure/injectable |
| D2 Weighted base+modifiers, clamp [0,10] | ✅ Yes | `scoring/engine.py` per design formula + bands |
| D3 Aggregate = max of open findings | ✅ Yes | Spec R3 + design D3 |
| D4 OpenAI SDK → Groq | ✅ Yes | ADR-005, lazy `AsyncOpenAI`, DB as cache (no Redis) |
| D5 reportlab for PDF | ✅ Yes | `reports/generator.py`, pure-Python Docker-safe |
| D6 Chained delivery ×5 | ✅ Yes | feature-branch-chain consolidated to main cd8d09c |
| Migration 004 additive | ✅ Yes | downgrade drops only added columns (verified by test) |
| Endpoint contract table | ✅ Yes | All 7 endpoints match design table incl. status domain `open\|resolved\|fp` |

Deviations (all documented in apply-progress, none break specs): scoring module path (`scoring/engine.py` package), `score()` signature includes `finding_type` (required for modifier table), remediation templates in RuleResult, clock injection `now` for TLS expiry determinism, tie-break `title.asc()` on equal scores, `top` clamp [1,100], malformed UUID → 404, missing `format` → 400 (not 422), CSV EOL `\n`.

## Issues Found

**CRITICAL**: None
**WARNING**: None
**SUGGESTION**:
- `pnpm lint` reports 7 pre-existing warnings (e.g. `hooks/use-mobile.ts` set-state-in-effect); not introduced by this change, but worth a follow-up cleanup.
- 2 backend skips are infrastructure-scoped (RLS, PostgreSQL-only) — expected.
- Vitest emits a Vite `configLoader: 'native'` ESM/CJS warning — benign, not a failure.
