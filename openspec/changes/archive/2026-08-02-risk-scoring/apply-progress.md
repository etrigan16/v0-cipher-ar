# Apply Progress — risk-scoring (PR 1: Phases 1-2)

- **Change**: risk-scoring
- **Batch**: PR 1 of feature-branch-chain (`feature/risk-scoring-p1` → tracker `feature/risk-scoring`)
- **Scope**: Phase 1 (Foundation) + Phase 2 (Rules + Scoring + Orchestrator). NO API routes, LLM, export, or frontend (Phases 3-7 are later PRs).
- **Mode**: Strict TDD (openspec/config.yaml `apply.tdd: true`; pytest 9.1.1, Python 3.11.9)
- **Artifact store**: hybrid
- **Date**: 2026-08-08
- **Commit range**: 27ff999 → f289519 (5 work-unit commits)

## Status

| Task | Status |
|------|--------|
| 1.1 Migration 004 (additive risk columns) | [x] |
| 1.2 Models Finding/Asset mirror columns | [x] |
| 1.3 Fingerprint header capture (HSTS/XCTO/CSP/Set-Cookie) | [x] |
| 1.4 TLS cert capture (not_before/not_after/issuer_cn) | [x] |
| 1.5 RED tests: migration + model + capture | [x] |
| 2.1 `finding_rules.py` (9 pure rules) | [x] |
| 2.2 RED: `tests/test_finding_rules.py` | [x] |
| 2.3 `scoring/engine.py` (base+modifiers, clamp, bands) | [x] |
| 2.4 RED: `tests/test_scoring.py` | [x] |
| 2.5 Orchestrator wires rules+scoring+persistence | [x] |
| 2.6 `recompute_asset_risk(db, asset_id)` extracted | [x] |
| 10. requirements.txt review | [x] no change needed (stdlib only; reportlab/openai are PR3/PR4) |

**11/11 tasks complete.** Ready for next batch (PR 2: API).

## Work Unit Evidence

| Work unit | Focused test command + result | Runtime harness + result | Rollback boundary |
|-----------|-------------------------------|--------------------------|-------------------|
| 1. Migration 004 + models | `pytest tests/test_migrations.py tests/test_asm.py -q` → 20 passed | Migration ops executed against real in-memory SQLite via `Operations.context` (upgrade + downgrade, legacy row preservation) | Revert commit 27ff999; `alembic downgrade 004_risk_scoring` drops only added columns |
| 2. Fingerprint capture | `pytest tests/test_discovery.py -q` → 17 passed | N/A — pure module (httpx/ssl faked per existing test design) | Revert commit 3a26a2e; fingerprint dict gains keys (additive) |
| 3. Finding rules | `pytest tests/test_finding_rules.py -q` → 22 passed | N/A — pure module, no I/O | Revert commit 80c2cc2; new module, no existing behavior touched |
| 4. Scoring engine | `pytest tests/test_scoring.py -q` → 16 passed | N/A — pure module, no I/O | Revert commit e8c56dc; new package |
| 5. Orchestrator wiring | `pytest tests/test_asm.py -q` → 23 passed | Real `run_scan` + real `/asm/scans` route over SQLite ASGITransport (network deps faked) | Revert commit f289519; orchestrator falls back to `fr.findings` semantics |

Full suite after all units: `pytest -q` → **110 passed, 2 skipped** (baseline was 58 passed, 2 skipped; +52 tests, 0 regressions).

## TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 1.1 Migration 004 | `tests/test_migrations.py` | Unit (migration ops) | ✅ 58/58 | ✅ Written | ✅ Passed | ✅ 2 cases (upgrade+rows, downgrade) | ➖ None needed |
| 1.2 Models | `tests/test_asm.py` | Unit (model) | ✅ 58/58 | ✅ Written | ✅ Passed | ✅ 2 cases (defaults, round-trip) | ➖ None needed |
| 1.3-1.4 Capture | `tests/test_discovery.py` | Unit | ✅ 58/58 | ✅ Written | ✅ Passed | ✅ 3 cases (full, multi-cookie, absent) | ✅ Cleaned header loop to mapping |
| 2.1-2.2 Rules | `tests/test_finding_rules.py` | Unit (pure) | N/A (new) | ✅ Written | ✅ Passed | ✅ 22 cases (fire/no-fire per rule) | ➖ None needed |
| 2.3-2.4 Scoring | `tests/test_scoring.py` | Unit (pure) | N/A (new) | ✅ Written | ✅ Passed | ✅ 16 cases (base/mod/clamp/bands/agg) | ➖ None needed |
| 2.5-2.6 Orchestrator | `tests/test_asm.py` | Integration | ✅ 58/58 | ✅ Written | ✅ Passed | ✅ 4 cases (scored persist, modifiers, max-of-open, re-scan) | ➖ None needed |

### Test Summary
- **Total tests written**: 52 (migration 2, model 3, discovery 6 new, rules 22, scoring 16, asm 3 new net)
- **Total tests passing**: 110 (full backend suite) / 2 skipped (RLS, PostgreSQL-only)
- **Layers used**: Unit (49), Integration (3 via ASGITransport)
- **Approval tests** (refactoring): 2 updated (`test_tls_fingerprint_from_fake_cert`, `test_scan_created_and_completed`, `test_stats_counts_only_own_tenant`)
- **Pure functions created**: `evaluate` + 9 rules, `score`, `risk_level_for`, `aggregate_risk`, `recompute_asset_risk` (async, DB-bound by design)

## Files Changed

| File | Action | What Was Done |
|------|--------|---------------|
| `backend/alembic/versions/004_risk_scoring.py` | Created | Additive migration: findings risk/enrichment/status columns + assets.risk_score; downgrade drops only those |
| `backend/app/models/finding.py` | Modified | Added risk_score/risk_level/finding_type/remediation/status/context/llm_summary/enriched_at |
| `backend/app/models/asset.py` | Modified | Added risk_score (nullable aggregate) |
| `backend/app/services/fingerprint.py` | Modified | Captures HSTS/XCTO/CSP/Set-Cookie (multi-value via get_list); TLS issuer_cn/not_before/not_after (ASN.1→ISO-Z) |
| `backend/app/services/finding_rules.py` | Created | 9 pure rules → RuleResult(finding_type, severity, title, detail, remediation); injectable `now` for expiry determinism |
| `backend/app/services/scoring/__init__.py` | Created | Public exports |
| `backend/app/services/scoring/engine.py` | Created | score/risk_level_for/aggregate_risk; base+modifiers, clamp [0,10], bands |
| `backend/app/services/orchestrator.py` | Modified | `_persist_findings` (delete prior + evaluate + score + persist); `recompute_asset_risk` |
| `backend/tests/test_migrations.py` | Created | Migration upgrade/downgrade against pre-004 schema (Operations.context) |
| `backend/tests/test_discovery.py` | Modified | Header/cert capture tests; `_FakeResponse` wraps headers in `httpx.Headers` |
| `backend/tests/test_finding_rules.py` | Created | 22 rule tests |
| `backend/tests/test_scoring.py` | Created | 16 scoring tests |
| `backend/tests/test_asm.py` | Modified | New model-column tests, orchestrator wiring tests, re-scan overwrite; fakes now drive rules via fingerprint dicts |

## Deviations from Design

1. **Scoring module path**: launch prompt said `backend/app/services/scoring.py`; tasks.md/design specify `app/services/scoring/engine.py`. Implemented as the package per tasks.md 2.3/design D2 (imports via `app.services.scoring.engine`).
2. **`score()` signature**: design formula says modifiers are keyed by `finding_type`, so the pure function takes `(severity, finding_type, fingerprint)` — `finding_type` is required for the modifier table. Spec R2's "pure over (severity, fingerprint)" is honored (pure, no I/O, deterministic).
3. **Remediation templates live in `finding_rules.RuleResult`** (one per rule) rather than in scoring (launch prompt task 7 wording); scoring stays a pure score function. This matches design's rule table and avoids duplicating templates with the PR3 LLM fallback.
4. **`evaluate(fingerprint, now=None)`**: clock injection added so the TLS-expiry rule is deterministic in tests; defaults to UTC now.
5. **Bands per design**: `0→info, <4→low, <7→medium, <9→high, ≥9→critical` (design.md) — the launch prompt's shorthand (0-2.9/3-5.9/6-7.9/8-10) omitted the `info` band; design is authoritative.
6. **Re-scan overwrite**: `_persist_findings` deletes the asset's prior findings before persisting new ones, implementing spec R3 "no history kept" — a behavior change from the previous append-only persistence (existing tests updated accordingly).

## Issues Found

- None blocking. One test-authoring correction during RED: a single finding has one `finding_type`, so "multiple modifiers stack" is impossible per-call; the clamp proof uses `critical + modifier` (10+1.5→10.0).

## Next Steps

- PR 2 (Phase 3 API): `GET /asm/findings`, `/asm/risk-summary`, `/asm/assets/{id}`, `PATCH /asm/findings/{id}`, `/asm/stats` risk fields, `tests/test_asm.py` extension.
- PR 3 (LLM), PR 4 (export), PR 5 (frontend) per tasks.md.
- Verify phase after all PRs; archive merges deltas.

---

# Apply Progress — risk-scoring (PR 2: Phase 3 API)

- **Change**: risk-scoring
- **Batch**: PR 2 of feature-branch-chain (`feature/risk-scoring-p2` → tracker `feature/risk-scoring`; base = `feature/risk-scoring-p1` @ 3e3b0df)
- **Scope**: Phase 3 (API) — tasks 3.1-3.6. NO LLM, export, or frontend (PRs 3-5).
- **Mode**: Strict TDD (openspec/config.yaml `apply.tdd: true`; pytest 9.1.1, Python 3.11.9)
- **Artifact store**: hybrid
- **Date**: 2026-08-08
- **Commit range**: 3e3b0df (p1 head) → b2b7874 (6 work-unit commits: 4d56da4, 4c45a00, 058c3d1, 377631d, dcdf60e, b2b7874)

## Status (Phase 3)

| Task | Status |
|------|--------|
| 3.1 `GET /asm/findings` — filters, `risk_score desc nullslast()`, limit/offset | [x] |
| 3.2 `GET /asm/risk-summary` — severity_counts, avg/max, open_findings, top 5; zeros when empty | [x] |
| 3.3 `GET /asm/assets/{id}` — asset + findings; cross-tenant/unknown 404 | [x] |
| 3.4 `PATCH /asm/findings/{id}` (`open`\|`resolved`\|`fp`) — invalid 422, recompute aggregate | [x] |
| 3.5 Extend `GET /asm/stats` risk fields | [x] |
| 3.6 Extend `tests/test_asm.py`: filters/sort, summary, asset 404, PATCH 422/404+recompute, stats, cross-tenant | [x] |

**6/6 Phase 3 tasks complete.** Cumulative: **17/17 tasks through Phase 3** (Phases 4-7 remain for PRs 3-5).

## Work Unit Evidence

| Work unit | Focused test command + result | Runtime harness + result | Rollback boundary |
|-----------|-------------------------------|--------------------------|-------------------|
| 1. Findings list (3.1) | `pytest tests/test_asm.py -k TestFindingsList -q` → 8 passed | Real routes over SQLite ASGITransport with `_patch_discovery`; filter/sort/pagination exercised end-to-end | Revert 4d56da4; additive (new endpoint + DTO risk fields) |
| 2. Risk summary (3.2) | `pytest tests/test_asm.py -k TestRiskSummary -q` → 4 passed | Same harness; real-data + empty-tenant summaries (200) | Revert 4c45a00; additive (new endpoint + shared `_risk_metrics`) |
| 3. Asset detail (3.3) | `pytest tests/test_asm.py -k TestAssetDetail -q` → 4 passed | Same harness; 200 / cross-tenant 404 / unknown 404 / 401 | Revert 058c3d1; additive |
| 4. Finding PATCH (3.4) | `pytest tests/test_asm.py -k TestFindingPatch -q` → 4 passed | Same harness; status flip verified through the real `/asm/assets` aggregate drop (`recompute_asset_risk`) | Revert 377631d; additive |
| 5. Stats risk fields (3.5) | `pytest tests/test_asm.py -k TestStats -q` → 3 passed | Same harness; legacy counts keep shape + risk fields present | Revert dcdf60e; additive keys |
| 6. Coverage completion (3.6) | `pytest tests/test_asm.py -q` → 44 passed | N/A — test-only unit (scan_id filter, top param) | Revert b2b7874; test-only |

Full suite after all units: `pytest -q` → **131 passed, 2 skipped** (PR1 baseline 110 passed, 2 skipped; +21 tests, 0 regressions).

## TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 3.1 Findings list | `tests/test_asm.py` | Integration | ✅ 23/23 | ✅ Written (7 failed) | ✅ Passed 8/8 | ✅ 8 cases (sort, status, severity, asset, pagination, scan_id, isolation, 401) | ✅ `_coerce_uuid` helper extracted; NULLS LAST + title tie-break |
| 3.2 Risk summary | `tests/test_asm.py` | Integration | ✅ 30/30 | ✅ Written (3 failed) | ✅ Passed 4/4 | ✅ 4 cases (real data, empty, top param, 401) | ✅ `_risk_metrics`/`_severity_counts` shared with stats |
| 3.3 Asset detail | `tests/test_asm.py` | Integration | ✅ 33/33 | ✅ Written (2 failed) | ✅ Passed 4/4 | ✅ 4 cases (owner, cross-tenant, unknown/malformed, 401) | ➖ None needed |
| 3.4 Finding PATCH | `tests/test_asm.py` | Integration | ✅ 37/37 | ✅ Written (3 failed) | ✅ Passed 4/4 | ✅ 4 cases (resolve+recompute, invalid 422, cross-tenant 404, 401) | ➖ None needed |
| 3.5 Stats risk fields | `tests/test_asm.py` | Integration (approval) | ✅ 41/41 | ✅ Approval updated → 2 failed | ✅ Passed 3/3 | ✅ 2 datasets (1-scan, 2-asset rich) | ➖ None needed |
| 3.6 Coverage completion | `tests/test_asm.py` | Integration | ✅ 42/42 | ✅ Written | ✅ Passed 2/2 | ✅ scan_id filter + top override | ➖ None needed |

### Test Summary (PR 2)
- **Total tests written**: 21 net new in `tests/test_asm.py` (findings 8, summary 4, asset 4, patch 4, stats 1) — 23 → 44
- **Total tests passing**: 131 (full backend suite) / 2 skipped (RLS, PostgreSQL-only)
- **Layers used**: Integration (21 via ASGITransport — all endpoints exercised end-to-end)
- **Approval tests** (refactoring): 1 updated (`test_stats_counts_only_own_tenant` — stats gained risk fields per spec)
- **Pure functions created**: none new (route-layer helpers `_coerce_uuid`, `_severity_counts`, `_risk_metrics` are async DB helpers by design)

## Files Changed (PR 2)

| File | Action | What Was Done |
|------|--------|---------------|
| `backend/app/routes/asm.py` | Modified | AssetDTO/FindingDTO + risk fields (risk_score, risk_level, finding_type, remediation, status, enriched_at); `_coerce_uuid`; `_severity_counts`/`_risk_metrics`; `GET /asm/findings`, `GET /asm/risk-summary`, `GET /asm/assets/{id}`, `PATCH /asm/findings/{id}` (Literal `open\|resolved\|fp`), stats risk fields |
| `backend/tests/test_asm.py` | Modified | `_seed_scans` helper (returns scan ids); TestFindingsList (8), TestRiskSummary (4), TestAssetDetail (4), TestFindingPatch (4), TestStats extended (2) |

## Deviations from Design

1. **PATCH status domain**: launch prompt said `open|resolved|false_positive`; spec R7 + design are authoritative — domain is `open|resolved|fp` (spec R7: "over the domain open|resolved|fp"). Implemented as Pydantic `Literal["open", "resolved", "fp"]` → invalid values 422.
2. **Tie-break ordering**: findings/asset lists add `title.asc()` after `risk_score.desc().nullslast()` for deterministic output on equal scores (design table only specified risk_score desc).
3. **`top` param clamp**: `top` on risk-summary clamps to [1, 100] (design said "top findings (default 5)"); default stays 5.
4. **Malformed UUID ids**: treated as 404 (asset/PATCH) or empty result (filters) via `_coerce_uuid` — design said "cross-tenant/unknown → 404" and "no data leak"; this extends the same guarantee to malformed ids without a 500.

## Issues Found

- None. One GREEN fix: `_risk_metrics` is async and was initially spread unawaited (`**await _risk_metrics(...)` corrected); caught by the risk-summary RED run.

## Next Steps

- PR 3 (Phase 4 LLM enrichment), PR 4 (Phase 5 export), PR 5 (Phase 6 frontend) per tasks.md.
- Phase 7 verification after all PRs; archive merges deltas.

## Cumulative Task Status (through PR 2)

| Phase | Tasks | Status |
|-------|-------|--------|
| Phase 1 Foundation | 1.1-1.5 | [x] all (PR 1) |
| Phase 2 Rules + Scoring | 2.1-2.6 | [x] all (PR 1) |
| Phase 3 API | 3.1-3.6 | [x] all (PR 2) |
| Phase 4 LLM Enrichment | 4.1-4.5 | [x] all (PR 3) |
| Phase 5 Export | 5.1-5.5 | [ ] pending (PR 4) |
| Phase 6 Frontend | 6.1-6.6 | [ ] pending (PR 5) |
| Phase 7 Verification | 7.1-7.2 | [ ] pending |

**22/24 implementation tasks complete through Phase 4.**

---

# Apply Progress — risk-scoring (PR 3: Phase 4 LLM Enrichment)

- **Change**: risk-scoring
- **Batch**: PR 3 of feature-branch-chain (`feature/risk-scoring-p3` → tracker `feature/risk-scoring`; base = `feature/risk-scoring-p2` @ 2cd6840)
- **Scope**: Phase 4 (LLM Enrichment) — tasks 4.1-4.5 + launch task "pin `openai` in requirements.txt". NO export (PR 4) or frontend (PR 5).
- **Mode**: Strict TDD (openspec/config.yaml `apply.tdd: true`; pytest 9.1.1, Python 3.11.9, openai 2.53.0)
- **Artifact store**: hybrid
- **Date**: 2026-08-08
- **Commit range**: 2cd6840 (p2 head) → ab6cf3b (3 work-unit commits: 84dcbcd, 4e340d6, ab6cf3b)

## Status (Phase 4)

| Task | Status |
|------|--------|
| 4.1 `app/config.py` + `.env.example`: `llm_api_key`/`llm_base_url`/`llm_model`/`llm_timeout` | [x] |
| 4.2 Create `app/services/llm/enrich.py`: lazy `AsyncOpenAI`, JSON `{remediation, context}`, shape validation, per-type templates | [x] |
| 4.3 `enrich_scan_findings()`: post-scan batch, skip enriched, per-finding try/except, `enriched_at` on templates | [x] |
| 4.4 `POST /asm/findings/{id}/enrich` — tenant 404 | [x] |
| 4.5 RED: `tests/test_llm_enrich.py` (mock): key absent→templates, failure→fallback, bad shape→fallback, enriched skipped | [x] |
| Launch: pin `openai` in `requirements.txt` | [x] (2.53.0; reportlab stays for PR 4) |

**5/5 Phase 4 tasks complete + launch openai pin.** Cumulative: **22/24 tasks through Phase 4** (Phases 5-7 remain for PRs 4-5 + verify).

## Work Unit Evidence

| Work unit | Focused test command + result | Runtime harness + result | Rollback boundary |
|-----------|-------------------------------|--------------------------|-------------------|
| 1. LLM config + openai pin (4.1) | `pytest tests/test_config.py -q` → 5 passed | Settings env resolution (`_env_file=None` + monkeypatch env) — no runtime boundary | Revert 84dcbcd; config defaults, keyless → `llm_enabled=False` (inert) |
| 2. Enrich service + batch wiring (4.2/4.3/4.5) | `pytest tests/test_llm_enrich.py -q` → 12 passed | Real `run_scan` over SQLite ASGITransport (`_patch_discovery`); findings enriched post-scan via templates (no key) | Revert 4e340d6; new package `llm/` + orchestrator call (additive; keyless → templates) |
| 3. On-demand endpoint (4.4) | `pytest tests/test_llm_enrich.py::TestOnDemandEnrichEndpoint -q` → 5 passed | Real `POST /asm/findings/{id}/enrich` over SQLite ASGITransport; 200/skip/404/404/401 exercised end-to-end | Revert ab6cf3b; additive endpoint + `asset_context` helper publicized |

Full suite after all units: `pytest -q` → **151 passed, 2 skipped** (PR2 baseline 131 passed, 2 skipped; +20 tests, 0 regressions).

## TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 4.1 Config | `tests/test_config.py` | Unit | ✅ 2/2 | ✅ Written (3 failed) | ✅ Passed 5/5 | ✅ 3 cases (defaults, key-derived enabled, env overrides) | ➖ None needed |
| 4.2 Enrich service | `tests/test_llm_enrich.py` | Unit | N/A (new) | ✅ Written (8 failed) | ✅ Passed 12/12 | ✅ 9 cases (template, determinism, unknown type, LLM success, failure, bad shape ×4, no-client) | ✅ Extracted `_build_prompt`, `_call_llm`, `_template_result` |
| 4.3 Batch + orchestrator | `tests/test_llm_enrich.py` | Integration | ✅ 44/44 | ✅ Written (1 failed) | ✅ Passed 12/12 | ✅ 5 cases (templates, LLM, skip-enriched, failure-continues, run_scan) | ✅ `asset_context` helper with per-batch cache |
| 4.4 Endpoint | `tests/test_llm_enrich.py` | Integration | ✅ 56/56 | ✅ Written (3 failed) | ✅ Passed 5/5 | ✅ 5 cases (success, skip, cross-tenant 404, unknown 404, 401) | ➖ None needed |

### Test Summary (PR 3)
- **Total tests written**: 20 net new (config 3, llm enrich 17)
- **Total tests passing**: 151 (full backend suite) / 2 skipped (RLS, PostgreSQL-only)
- **Layers used**: Unit (8), Integration (12 via ASGITransport — batch + endpoint exercised end-to-end)
- **Approval tests** (refactoring): None — no existing behavior changed; orchestrator gained a guarded post-scan call
- **Pure functions created**: `_build_prompt`, `_template_result` (pure); `enrich_finding`/`enrich_scan_findings`/`asset_context` are async service fns by design

## Files Changed (PR 3)

| File | Action | What Was Done |
|------|--------|---------------|
| `backend/app/config.py` | Modified | `llm_api_key` (default ""), `llm_base_url` (Groq), `llm_model` (llama-3.3-70b-versatile), `llm_timeout` (30.0), `llm_enabled` property derived from key presence |
| `backend/.env.example` | Modified | Documented optional `LLM_*` env vars |
| `backend/requirements.txt` | Modified | Pinned `openai==2.53.0` (reportlab deferred to PR 4) |
| `backend/app/services/llm/__init__.py` | Created | Package exports |
| `backend/app/services/llm/enrich.py` | Created | `enrich_finding` (LLM/template, never raises), `enrich_scan_findings` (batch, skip-enriched, per-finding try/except), `asset_context`, `_build_prompt`, `_template_result`, `_call_llm` (shape validation) |
| `backend/app/services/orchestrator.py` | Modified | `run_scan` calls `enrich_scan_findings` post-persist/scoring; guarded so enrichment never fails a scan (spec R1) |
| `backend/app/routes/asm.py` | Modified | `POST /asm/findings/{id}/enrich` — tenant-scoped, 404 on cross-tenant/unknown/malformed, skip-enriched returns current |
| `backend/tests/test_config.py` | Modified | 3 new LLM-config tests |
| `backend/tests/test_llm_enrich.py` | Created | 17 tests: templates, LLM success/failure/bad-shape (mocked client), skip-enriched, batch, orchestrator wiring, endpoint (401/404/success/skip) |

## Deviations from Design

1. **No migration 005**: the launch prompt said "prefer new migration 005_llm_enrichment.py" BUT also "check alembic history first" — history shows the alembic head is `004_risk_scoring`, which **already** added `context`, `llm_summary`, `enriched_at`, `remediation` (PR 1, tasks 1.1). The columns exist; a 005 would be a no-op duplicate. No new migration was created.
2. **Field naming**: launch prompt listed `enriched_description`/`enriched_remediation`; spec R3/design/model are authoritative — the Finding model already has `remediation`, `context`, `llm_summary`, `enriched_at` (migration 004), so enrichment persists into those exact columns.
3. **Module path**: launch prompt said `app/services/llm.py`; tasks.md 4.2/design/exploration specify `app/services/llm/enrich.py` (package) — implemented per tasks.md/design.
4. **`asset_context` made public**: `_asset_context` was renamed to `asset_context` so the on-demand route can build the prompt context without reaching into a private helper.
5. **`llm_enabled` derived**: added as a `Settings` property (not a stored field) per launch prompt "LLM_ENABLED derived from key presence".

## Issues Found

- None blocking. Two RED-era test corrections: (a) `_make_finding(tenant=None)` initially failed on `tenant.id` — unit-test findings now use a fixed dummy tenant uuid (never persisted); (b) `test_batch_skips_already_enriched` first asserted `calls == []` but the second finding IS legitimately enriched via the fake client — corrected to `len(calls) == 1`.

## Next Steps

- PR 4 (Phase 5 export): `reports/generator.py` CSV+PDF (reportlab), `GET /asm/export`, pin `reportlab`.
- PR 5 (Phase 6 frontend): `lib/api.ts`, dashboard charts, findings page with PATCH UI.
- Phase 7 verification after all PRs; archive merges deltas.

## Cumulative Task Status (through PR 3)

| Phase | Tasks | Status |
|-------|-------|--------|
| Phase 1 Foundation | 1.1-1.5 | [x] all (PR 1) |
| Phase 2 Rules + Scoring | 2.1-2.6 | [x] all (PR 1) |
| Phase 3 API | 3.1-3.6 | [x] all (PR 2) |
| Phase 4 LLM Enrichment | 4.1-4.5 | [x] all (PR 3) |
| Phase 5 Export | 5.1-5.5 | [ ] pending (PR 4) |
| Phase 6 Frontend | 6.1-6.6 | [ ] pending (PR 5) |
| Phase 7 Verification | 7.1-7.2 | [ ] pending |

**22/24 implementation tasks complete through Phase 4.**

---

# Apply Progress — risk-scoring (PR 4: Phase 5 Export)

- **Change**: risk-scoring
- **Batch**: PR 4 of feature-branch-chain (`feature/risk-scoring-p4` → tracker `feature/risk-scoring`; base = `feature/risk-scoring-p3` @ 52de078)
- **Scope**: Phase 5 (Export) — tasks 5.1-5.5 + launch task "pin `reportlab`". NO frontend (PR 5).
- **Mode**: Strict TDD (openspec/config.yaml `apply.tdd: true`; pytest 9.1.1, Python 3.11.9, reportlab 5.0.0)
- **Artifact store**: hybrid
- **Date**: 2026-08-08
- **Commit range**: 52de078 (p3 head) → e7e58e9 (2 work-unit commits: 653887c, e7e58e9)

## Status (Phase 5)

| Task | Status |
|------|--------|
| 5.1 Create `app/services/reports/generator.py`: `generate_csv()` — stdlib, headers asset/title/severity/risk_score/status/remediation/discovered_at, headers-only when empty | [x] |
| 5.2 `generate_pdf(findings, tenant_name)` — reportlab platypus, title/severity dist/avg-max/top findings+remediation, zeroed when empty | [x] |
| 5.3 `GET /asm/export?format=csv\|pdf` — Content-Type/Disposition; bad format 400 | [x] |
| 5.4 RED: `tests/test_export.py` — CSV headers/UTF-8, PDF `%PDF`, empty, tenant scoping | [x] |
| 5.5 Pin `reportlab` in `requirements.txt` (`openai` was pinned in PR 3) | [x] (reportlab==5.0.0) |

**5/5 Phase 5 tasks complete.** Cumulative: **27/27 tasks through Phase 5** (Phases 6-7 remain for PR 5 + verify).

## Work Unit Evidence

| Work unit | Focused test command + result | Runtime harness + result | Rollback boundary |
|-----------|-------------------------------|--------------------------|-------------------|
| 1. Report generators + reportlab pin (5.1/5.2/5.5) | `pytest tests/test_export.py -k "TestCsvGenerator or TestPdfGenerator" -q` → 7 passed | Real `generate_pdf`/`generate_csv` run in-process; PDF bytes verified `%PDF` + text extraction (ASCII85→Flate decode) | Revert 653887c; new package `reports/` + pin (additive; no existing behavior touched) |
| 2. Export endpoint (5.3) | `pytest tests/test_export.py::TestExportEndpoint -q` → 7 passed | Real `GET /asm/export` over SQLite ASGITransport with `_patch_discovery`/`_seed_scans`; 200 csv/pdf, 400 invalid+missing, 401, empty, cross-tenant isolation end-to-end | Revert e7e58e9; additive endpoint, no existing route touched |

Full suite after all units: `pytest -q` → **165 passed, 2 skipped** (PR3 baseline 151 passed, 2 skipped; +14 tests, 0 regressions).

## TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 5.1 CSV generator | `tests/test_export.py::TestCsvGenerator` | Unit (pure) | N/A (new) | ✅ Written (collection error — module absent) | ✅ Passed 5/5 | ✅ 5 cases (headers/empty, values, escaping, UTF-8, unscored) | ➖ None needed |
| 5.2 PDF generator | `tests/test_export.py::TestPdfGenerator` | Unit (pure) | N/A (new) | ✅ Written (2 failed — extraction helper) | ✅ Passed 2/2 | ✅ 2 cases (real data w/ exact avg/max, empty zeroed) | ✅ Decode helper generalized to ASCII85+Flate after RED |
| 5.3 Export endpoint | `tests/test_export.py::TestExportEndpoint` | Integration | ✅ 44/44 (test_asm) | ✅ Written (7 failed — route 404) | ✅ Passed 7/7 | ✅ 7 cases (csv, pdf, invalid 400, missing 400, 401, empty, tenant scope) | ➖ None needed |

### Test Summary (PR 4)
- **Total tests written**: 14 net new in `tests/test_export.py` (CSV 5, PDF 2, endpoint 7)
- **Total tests passing**: 165 (full backend suite) / 2 skipped (RLS, PostgreSQL-only)
- **Layers used**: Unit (7 via pure generators), Integration (7 via ASGITransport)
- **Approval tests** (refactoring): None — no existing behavior changed
- **Pure functions created**: `generate_csv`, `generate_pdf`, `_fmt_number`, `_fmt_datetime` (pure); endpoint is async DB-bound by design

## Files Changed (PR 4)

| File | Action | What Was Done |
|------|--------|---------------|
| `backend/requirements.txt` | Modified | Pinned `reportlab==5.0.0` (pure-Python, slim-Docker-safe; openai pin from PR 3 untouched) |
| `backend/app/services/reports/__init__.py` | Created | Package exports: `ExportFinding`, `generate_csv`, `generate_pdf` |
| `backend/app/services/reports/generator.py` | Created | `ExportFinding` dataclass; `generate_csv` (stdlib csv, fixed R1 headers, `\n` EOL, headers-only when empty); `generate_pdf` (reportlab platypus A4 — dark title band, Risk Summary with severity distribution + avg/max, findings table sorted by risk desc incl. remediation, zeroed metrics + no-findings note when empty); `_fmt_number`/`_fmt_datetime` |
| `backend/app/routes/asm.py` | Modified | `GET /asm/export?format=csv\|pdf` — tenant-scoped join with Asset, 400 on invalid/missing format, `Response` with text/csv or application/pdf + attachment Content-Disposition; imports `Response`, `Tenant`, reports package |
| `backend/tests/test_export.py` | Created | 14 tests: CSV headers/values/escaping/UTF-8/unscored-empty-cell; PDF `%PDF` + text-token extraction (ASCII85→Flate decode helper) for real/empty data; endpoint csv/pdf 200 + content-type + disposition, invalid/missing 400, 401, empty export, cross-tenant isolation |

## Deviations from Design

1. **CSV header set**: launch prompt listed columns `(severity, risk_score, title, asset, detail, remediation, status, discovered_at)`; spec R1 + design Export section are authoritative — implemented exactly as `asset, finding title, severity, risk_score, status, remediation, discovered_at` (no `detail` column, per design).
2. **Function names**: launch prompt uses `generate_csv(findings)` / `generate_pdf(findings, tenant_name)`; tasks.md 5.1/5.2 call them `csv_report()`/`pdf_report()`. Implemented per the launch prompt (the operative PR-4 instruction); `reports/__init__.py` re-exports them.
3. **PDF findings table includes a remediation column** (Severity, Risk Score, Title, Asset, Status, Remediation) — the prompt enumerated 5 columns, but spec R2 requires "top findings with remediation"; the column satisfies both.
4. **PDF summary includes max risk** alongside avg (prompt said "counts by severity, avg risk") — spec R2 requires "average and maximum risk".
5. **Missing `format` → 400**: spec R3 says "invalid or missing format MUST return 400"; implemented `format: str | None` with a manual 400 check (a `Literal` param would yield 422 instead).
6. **CSV EOL normalized to `\n`** for deterministic cross-platform output (RFC 4180 default `\r\n` varies by OS).

## Issues Found

- **reportlab 5.0 encodes content streams with `[ /ASCII85Decode /FlateDecode ]`** (the stream is ASCII85-encoded then zlib-compressed, and there is no newline before `endstream`). The RED PDF tests initially failed on the raw-extraction helper; fixed by generalizing `_decode_pdf_stream` to try ASCII85→Flate, bare Flate, then raw. This is test-side only — the generated PDFs are valid (viewers decode the standard filter chain).
- One test-authoring bug during RED: `_pdf_text_tokens` called `base64.a85decode` before `import base64` — the NameError was silently swallowed by the decode fallback chain; fixed by importing `base64`.

## Next Steps

- PR 5 (Phase 6 frontend): `lib/api.ts` export URL + findings/dashboard UI with PATCH.
- Phase 7 verification after all PRs; archive merges deltas.

## Cumulative Task Status (through PR 4)

| Phase | Tasks | Status |
|-------|-------|--------|
| Phase 1 Foundation | 1.1-1.5 | [x] all (PR 1) |
| Phase 2 Rules + Scoring | 2.1-2.6 | [x] all (PR 1) |
| Phase 3 API | 3.1-3.6 | [x] all (PR 2) |
| Phase 4 LLM Enrichment | 4.1-4.5 | [x] all (PR 3) |
| Phase 5 Export | 5.1-5.5 | [x] all (PR 4) |
| Phase 6 Frontend | 6.1-6.6 | [ ] pending (PR 5) |
| Phase 7 Verification | 7.1-7.2 | [ ] pending |

**27/29 tasks complete through Phase 5.**

---

# Apply Progress — risk-scoring (PR 5: Phases 6-7 Frontend + Verification)

- **Change**: risk-scoring
- **Batch**: PR 5 of feature-branch-chain (`feature/risk-scoring-p5` → tracker `feature/risk-scoring`; base = `feature/risk-scoring-p4` @ 5047955)
- **Scope**: Phase 6 (Frontend) + Phase 7 (Verification) — the FINAL slice of the change. Tasks 6.1-6.6 + 7.1-7.2.
- **Mode**: Strict TDD (openspec/config.yaml `apply.tdd: true`; vitest 4.1.10, recharts 2.15.0, React 19)
- **Artifact store**: hybrid
- **Date**: 2026-08-08
- **Commit range**: 5047955 (p4 head) → HEAD (6 work-unit commits: b18b08d, chart commit, e3579a3, findings page, 3c5bb68, 4de6bf1 + this docs commit)

## Status (Phases 6-7)

| Task | Status |
|------|--------|
| 6.1 `lib/api.ts`: Finding/Asset risk fields + `getFindings`, `getRiskSummary`, `getAsset`, `patchFinding`, `enrichFinding`, `exportFindings` (blob) + `buildHeaders` extraction | [x] |
| 6.2 `components/charts/risk-distribution.tsx` (recharts severity chart, `severityCounts` prop, pure `buildSeverityData`) | [x] |
| 6.3 `app/dashboard/findings/page.tsx` — filterable table, severity badge, risk score, asset name, status, PATCH open/resolved/fp, enrich, CSV/PDF export | [x] |
| 6.4 `app/dashboard/attack-surface/page.tsx` — `risk_score` column (dash for unscored) | [x] |
| 6.5 `app/dashboard/page.tsx` risk summary section (severity chart + avg risk + open findings + findings link); `app/dashboard/layout.tsx` Findings nav link | [x] |
| 6.6 RED tests: `lib/api.test.ts` (+12), `components/charts/risk-distribution.test.tsx` (5), `app/dashboard/page.test.tsx` (+3), `app/dashboard/findings/page.test.tsx` (9), `app/dashboard/layout.test.tsx` (2), attack-surface (+2) | [x] |
| 7.1 Full suite green: pytest 165 passed/2 skipped; pnpm test 75 passed; tsc --noEmit clean; pnpm lint 0 errors (7 pre-existing warnings) | [x] |
| 7.2 Manual smoke: `pnpm dev` boots clean; `/`, `/dashboard`, `/dashboard/findings` serve 200 with no compile errors; export blob download verified by automated tests | [x] |

**8/8 Phase 6-7 tasks complete.** Cumulative: **29/29 tasks complete — the whole risk-scoring change.**

## Work Unit Evidence

| Work unit | Focused test command + result | Runtime harness + result | Rollback boundary |
|-----------|-------------------------------|--------------------------|-------------------|
| 1. api.ts endpoints (6.1) | `pnpm vitest run lib/api.test.ts` → 24 passed (12 new) | Mocked fetch (vi.stubGlobal) — URL/method/body/auth-header/blob asserted per function; blob path exercised with a real `res.blob()` | Revert b18b08d; additive — new functions + types, `buildHeaders` preserves existing `request()` header order (approval tests 12/12) |
| 2. Risk distribution chart (6.2) | `pnpm vitest run components/charts/risk-distribution.test.tsx` → 5 passed | Real recharts BarChart render in jsdom — SVG bars present, accessible aria-label reflects counts | Revert chart commit; new component + pure fn, no existing behavior touched |
| 3. Dashboard risk summary (6.5) | `pnpm vitest run app/dashboard/page.test.tsx` → 6 passed (3 new) | Dashboard rendered with URL-routed fetch mock; chart + avg/open cards + findings link asserted; existing stat-card tests (3) kept green via zeroed fallback | Revert e3579a3; additive section, defensive zeroing keeps legacy responses readable |
| 4. Findings page (6.3) | `pnpm vitest run app/dashboard/findings/page.test.tsx` → 9 passed | Full page render in jsdom with routed fetch: list, filters, PATCH, enrich, CSV/PDF blob download (URL.createObjectURL + anchor click spied), empty + error states | Revert findings-page commit; new page + route, no other page touched |
| 5. Nav link + attack-surface (6.4) | `pnpm vitest run app/dashboard/layout.test.tsx app/dashboard/attack-surface/page.test.tsx` → 8 passed (4 new) | Layout renders with mocked auth/router/link; attack-surface renders scored (9.5) and unscored (dash) assets | Revert 3c5bb68; additive nav entry + column |
| 6. Lint refactor | `pnpm vitest run app/dashboard/findings/page.test.tsx` → 9 passed; `pnpm lint` → 0 errors | Findings page refetched via `.then` callbacks matching dashboard pattern; `react-hooks/set-state-in-effect` warning eliminated | Revert 4de6bf1; behavior identical, tests unchanged |

Full suite after all units: `pnpm test` → **75 passed (11 files)** (baseline 42; +33 tests, 0 regressions); `cd backend && pytest -q` → **165 passed, 2 skipped** (unchanged — frontend-only PR).

## TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 6.1 api.ts | `lib/api.test.ts` | Unit (mocked fetch) | ✅ 12/12 | ✅ Written (12 failed) | ✅ Passed 24/24 | ✅ 12 cases (urls, filters, body, auth, blob, errors) | ✅ `buildHeaders` extracted; `request` approval 12/12 |
| 6.2 Chart | `components/charts/risk-distribution.test.tsx` | Unit (component) | N/A (new) | ✅ Written (import error) | ✅ Passed 5/5 | ✅ 5 cases (order, zero-fill, 3 aria-label variants, bars drawn) | ✅ SEVERITY_ORDER/COLORS constants; `isAnimationActive=false` fix |
| 6.5 Dashboard | `app/dashboard/page.test.tsx` | Integration (component) | ✅ 3/3 | ✅ Written (3 failed) | ✅ Passed 6/6 | ✅ 3 cases (real data, failure→zeros, link) | ✅ YAxis tick text hidden to keep text queries deterministic |
| 6.3 Findings page | `app/dashboard/findings/page.test.tsx` | Integration (component) | N/A (new) | ✅ Written (import error) | ✅ Passed 9/9 | ✅ 9 cases (list, 2 filters, PATCH, enrich, 2 exports, empty, error) | ✅ effect fetch → `.then` pattern (lint); `assetName` memoized |
| 6.4 Layout + attack-surface | `layout.test.tsx`, `attack-surface/page.test.tsx` | Integration (component) | ✅ 4/4 | ✅ Written (3 failed) | ✅ Passed 8/8 | ✅ 3 cases (nav link, kept links, scored + unscored) | ➖ None needed |

### Test Summary (PR 5)
- **Total tests written**: 33 net new (api 12, chart 5, dashboard 3, findings 9, layout 2, attack-surface 2)
- **Total tests passing**: 75 frontend (full suite) / 165 backend (2 skipped: RLS, PostgreSQL-only)
- **Layers used**: Unit (17 via mocked fetch + pure fn), Integration (16 via component render with routed fetch)
- **Approval tests** (refactoring): 12 api.ts existing tests kept green after `buildHeaders` extraction; 3 dashboard tests kept green after risk-section wiring; 4 attack-surface tests kept green after the risk column
- **Pure functions created**: `buildSeverityData` (chart data mapping); `buildHeaders` (shared fetch headers)

## Files Changed (PR 5)

| File | Action | What Was Done |
|------|--------|---------------|
| `lib/api.ts` | Modified | Asset.risk_score, Finding risk/enrichment/status fields; `SeverityCounts`, `RiskSummary`, `FindingsList`, `AssetDetail`, `FindingStatus`, `FindingsFilters` types; `getFindings` (filter query serialization), `getRiskSummary`, `getAsset`, `patchFinding`, `enrichFinding`, `exportFindings` (blob download); `buildHeaders` shared helper |
| `lib/api.test.ts` | Modified | +12 tests: URL/method/body/auth/filter-serialization/blob/error propagation for the new endpoints |
| `components/charts/risk-distribution.tsx` | Created | recharts BarChart of severity distribution; fixed critical-first order, per-severity Cell colors, accessible `role="img"` aria-label summary; `buildSeverityData` pure mapping |
| `components/charts/risk-distribution.test.tsx` | Created | 5 tests: order, zero-fill, accessible summary from counts, bars drawn, triangulated counts |
| `app/dashboard/page.tsx` | Modified | Risk summary section: severity chart + avg risk + open findings + "Ver hallazgos" link; defensive zeroing; second fetch for risk-summary |
| `app/dashboard/page.test.tsx` | Modified | +3 tests: risk summary render, findings link, failure→zeros (URL-routed fetch) |
| `app/dashboard/findings/page.tsx` | Created | Filterable findings table (severity/risk/title/asset/status/enriched), native selects, per-row PATCH open/resolved/fp + enrich buttons, CSV/PDF blob export buttons, empty/error/loading states; asset names resolved via client-side listAssets map |
| `app/dashboard/findings/page.test.tsx` | Created | 9 tests: list, severity/status filters, PATCH resolve + row update, enrich + enriched date, CSV/PDF download (createObjectURL/click spied), empty, error |
| `app/dashboard/layout.tsx` | Modified | Findings sidebar nav link (ListChecks icon) between Attack Surface and Phishing |
| `app/dashboard/layout.test.tsx` | Created | 2 tests: findings link href, existing links preserved (mocked auth/router/link) |
| `app/dashboard/attack-surface/page.tsx` | Modified | Risk score column (dash for unscored) |
| `app/dashboard/attack-surface/page.test.tsx` | Modified | +2 tests: scored (9.5) and unscored (dash) rendering |
| `openspec/changes/risk-scoring/tasks.md` | Modified | Phases 6-7 marked [x] (all 29 tasks complete) |

## Deviations from Design

1. **Chart component path**: launch prompt said `components/charts/risk-distribution.tsx`; tasks.md 6.2 said `components/dashboard/{severity-chart,risk-cards,top-findings}.tsx`. Implemented per the launch prompt (operative PR-5 instruction): one reusable chart component with a `severityCounts` prop; the dashboard risk section renders the chart plus avg-risk/open-findings cards and the findings link inline (no separate risk-cards/top-findings files). Behavior matches design's dashboard goals (severity distribution + risk metrics).
2. **Findings API naming**: launch prompt `getFindings`/`exportFindings`; tasks.md 6.1 said `listFindings`/`exportUrl`. Launch prompt wins (consistent with the chain's established pattern). `exportFindings(format)` returns a `Blob` and the page triggers the download via object URL + anchor click.
3. **Asset name column**: FindingDTO carries `asset_id` only (no asset name), so the findings page resolves names via a client-side `listAssets()` map (subdomain ?? domain, "—" fallback). No backend change — this PR is frontend-only.
4. **tasks.md 6.4 attack-surface**: not in the launch prompt's task list, but design.md requires the `risk_score` column and this is the FINAL PR — implemented the column (additive, small) so the change completes; noted here for transparency. "Inline asset detail" from design was not implemented (launch-prompt scope is authoritative; would expand the diff beyond this slice).
5. **Dashboard risk section scope**: launch prompt asked for chart + avg risk + open findings only; design also mentioned top findings and max-risk cards — omitted per the operative launch-prompt scope (risk-summary top_findings/max_risk remain available on the API for future UI).
6. **YAxis tick text hidden** on the chart: keeps the SVG free of numeric text that collides with page-level text queries and keeps jsdom rendering deterministic; exact counts remain in the Tooltip and the aria-label.
7. **`isAnimationActive={false}`** on the Bar: recharts 2.15.0 + React 19 renders empty `recharts-bar-rectangle` groups with Cell fills when animation is on (observed in jsdom); disabling entrance animation fixes deterministic rendering.

## Issues Found

- **recharts 2.15.0 + React 19 jsdom gotcha**: `<Bar>` with `<Cell>` children and default animation renders empty bar groups; fixed with `isAnimationActive={false}`. Also: rounded `radius` bars are SVG `<path>`s, not `<rect>`s (test assertions count both).
- **Transient vitest forks-pool worker timeouts** on the first cold `pnpm test` run on this Windows machine (7 worker errors, 1 file passed); a clean re-run passed 8/8 files. Infrastructure flakiness, not a test failure.
- **Native select option labels** must be Spanish ("Abiertos", "Alta", …) so status/severity badge text ("open", "high") stays unique for `getByText` queries.

## Next Steps

- All 29 tasks complete. The change is ready for **sdd-verify** (final verification) and then **sdd-archive** (merge deltas into main specs).
- Tracker PR `feature/risk-scoring` aggregates PRs 1-5 to `main` once reviewed.

## Cumulative Task Status (FINAL)

| Phase | Tasks | Status |
|-------|-------|--------|
| Phase 1 Foundation | 1.1-1.5 | [x] all (PR 1) |
| Phase 2 Rules + Scoring | 2.1-2.6 | [x] all (PR 1) |
| Phase 3 API | 3.1-3.6 | [x] all (PR 2) |
| Phase 4 LLM Enrichment | 4.1-4.5 | [x] all (PR 3) |
| Phase 5 Export | 5.1-5.5 | [x] all (PR 4) |
| Phase 6 Frontend | 6.1-6.6 | [x] all (PR 5) |
| Phase 7 Verification | 7.1-7.2 | [x] all (PR 5) |

**29/29 tasks complete — risk-scoring change fully implemented.**
