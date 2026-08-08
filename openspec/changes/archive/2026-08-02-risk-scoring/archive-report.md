# Archive Report: risk-scoring

**Change**: risk-scoring (Risk Scoring, LLM Enrichment, Findings Dashboard & Export — Sprint 2)
**Archived**: 2026-08-02
**Archive path**: `openspec/changes/archive/2026-08-02-risk-scoring/`
**Artifact store**: hybrid (Engram + OpenSpec filesystem)
**Delivery strategy**: chained (feature-branch-chain), 5 PR slices consolidated to `main` (`cd8d09c`), deployed to www.aukalabs.com

## Cycle Outcome

| Metric | Value |
|--------|-------|
| Requirements | 19/19 PASS |
| Scenarios | 46/46 PASS |
| Tasks (persisted tasks.md) | 35/35 complete (0 unchecked) |
| Backend tests | 165 passed / 2 skipped (RLS/PostgreSQL-only) |
| Frontend tests | 75 passed (11 files) |
| Type-check (`tsc --noEmit`) | clean, exit 0 |
| Lint | 0 errors (7 pre-existing warnings in untouched files) |
| Build (`pnpm build`) | exit 0 |
| Verdict | PASS (native `sdd-verify-validate` admitted `verdict: pass`) |
| Evidence revision | `sha256:cc88ed56ca250d8422612cdd6a959c82a050936c328022651751af3587d70aea` |
| New capabilities | 3 (risk-scoring, llm-enrichment, report-export) + attack-surface delta |

## Task Completion Gate

The persisted `tasks.md` shows **0 unchecked implementation tasks** (35/35 `[x]` across Phases 1–7). No reconciliation was required.

**Reported count discrepancy (recorded explicitly, not resolved silently)**: the launch prompt and the `verify-report.md` headline state "29/29 tasks complete", while the persisted tasks artifact contains 35 checked tasks (Phase 1: 5, Phase 2: 6, Phase 3: 6, Phase 4: 5, Phase 5: 5, Phase 6: 6, Phase 7: 2 = 35). The `verify-report.md`'s own PR-slice breakdown (11/11 PR1 + 6/6 PR2 + 5/5 PR3 + 5/5 PR4 + 8/8 PR5 = 35) corroborates the tasks artifact. Per the Final-State Authority hierarchy, the persisted tasks artifact is the higher-ranked source for completion visibility, so this report records **35/35 complete, 0 unchecked** and flags the "29" figure in the launch prompt / verify-report as an undercount of the same completed set. Completion state is unambiguous in both sources: 100% complete, 0 pending.

## Native Review Gate (Maintainer-Authorized)

**MAINTAINER-AUTHORIZED DECISION**: `reviewGate.delivery: disabled/unmanaged` for this change — the kill switch is off and no native review governs this change (consistent with the prior changes: `attack-surface-core`, `mfa-auth`, `multi-tenant-rls`, `ci-pipeline`, `waitlist-api`, `docs-sync-pricing`).

Per the Native Review Receipt Gate, `disabled/unmanaged` is the only relaxation and it was explicitly authorized by the maintainer in the archive launch prompt. The SDD verify PASS (native `sdd-verify-validate` admitted `verdict: pass`, evidence_revision `sha256:cc88ed56…`) is the quality gate for this change.

No `review.reset` or any review transaction was attempted — this is a deliberate maintainer decision. No review artifacts exist for this change (no `reviews/` directory in the change folder, no `sdd/risk-scoring/review/*` Engram topics), consistent with the disabled/unmanaged state.

## Spec Sync

| Domain | Action | Details |
|--------|--------|---------|
| `risk-scoring` | Created (new domain) | Full spec copied verbatim from delta: 7 requirements, 19 scenarios. Diff verified IDENTICAL after archive move. |
| `llm-enrichment` | Created (new domain) | Full spec copied verbatim from delta: 4 requirements, 10 scenarios. Diff verified IDENTICAL. |
| `report-export` | Created (new domain) | Full spec copied verbatim from delta: 4 requirements, 8 scenarios. Diff verified IDENTICAL. |
| `attack-surface` | Updated (delta on existing spec) | MODIFIED `Asset Model` (+`risk_score` column, +"risk_score nullable on legacy rows" scenario) and `Finding Model` (+risk/enrichment columns, +"New columns default safely" scenario) replaced in place; ADDED `Additive Risk Scoring Migration 004` and `Stats Risk Fields` appended. All 8 other requirements (Scan Model, Trigger Scan, List Assets, Scan Results, Subdomain Enumeration, Active Fingerprinting, Multi-tenant RLS, Frontend Dashboard) preserved unchanged. |

`openspec/config.yaml` `rules.archive` ("Warn before merging destructive deltas") — not triggered: the merge is additive (2 modified in place + 2 appended; no removals), and the new-domain copies are non-destructive.

## Engram Traceability (Observation IDs)

| Artifact | Engram ID | Sync ID |
|----------|-----------|---------|
| proposal | #115 | obs-b0d410027c5bb1f6 |
| spec | #116 | obs-0b14cf842d64d42e |
| design | #117 | obs-86f886bde12cf57d |
| tasks | #123 | obs-8f84c1dbfc5c1f11 |
| apply-progress | #124 | obs-f124a85ba7b51fa7 |
| verify-report | #136 | obs-2fe722f050428738 |
| archive-report | (this report) | — |
| review/* | none | none (disabled/unmanaged per maintainer authorization) |

## Archive Verification Checklist

- [x] Main specs updated: `openspec/specs/risk-scoring/spec.md`, `openspec/specs/llm-enrichment/spec.md`, `openspec/specs/report-export/spec.md` created (byte-identical to deltas); `openspec/specs/attack-surface/spec.md` merged (2 MODIFIED + 2 ADDED, 8 preserved)
- [x] Change folder moved: `openspec/changes/risk-scoring/` → `openspec/changes/archive/2026-08-02-risk-scoring/`
- [x] Archive contains all artifacts: proposal.md, exploration.md, specs/{risk-scoring,llm-enrichment,report-export,attack-surface}/spec.md, design.md, tasks.md, apply-progress.md, verify-report.md, archive-report.md
- [x] Archived `tasks.md`: 35/35 checked, 0 unchecked implementation tasks
- [x] Active changes directory no longer contains this change

## Known Notes / Suggestions (carried from verify, non-blocking)

1. `pnpm lint` reports 7 pre-existing warnings (e.g. `hooks/use-mobile.ts` set-state-in-effect) — not introduced by this change; worth a follow-up cleanup.
2. 2 backend test skips are infrastructure-scoped (RLS, PostgreSQL-only) — expected.
3. Vitest emits a Vite `configLoader: 'native'` ESM/CJS warning — benign, not a failure.
4. Coverage not measured (`coverage_threshold: 0` in config) — no threshold configured.
5. Documented deviations (all in apply-progress, none break specs): scoring module path (`scoring/engine.py` package), `score()` signature includes `finding_type`, remediation templates in RuleResult, clock injection `now` for TLS expiry determinism, tie-break `title.asc()` on equal scores, `top` clamp [1,100], malformed UUID → 404, missing `format` → 400 (not 422), CSV EOL `\n`.

## SDD Cycle Complete

The change has been fully planned, implemented, verified, and archived. No CRITICAL or WARNING findings remain. Ready for the next change.
