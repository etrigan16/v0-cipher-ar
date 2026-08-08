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
| Phase 4 LLM Enrichment | 4.1-4.5 | [ ] pending (PR 3) |
| Phase 5 Export | 5.1-5.5 | [ ] pending (PR 4) |
| Phase 6 Frontend | 6.1-6.6 | [ ] pending (PR 5) |
| Phase 7 Verification | 7.1-7.2 | [ ] pending |

**17/24 implementation tasks complete through Phase 3.**
