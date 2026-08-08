# Archive Report: attack-surface-core

**Change**: attack-surface-core (Attack Surface Manager — Sprint 1 Core)
**Archived**: 2026-08-02
**Archive path**: `openspec/changes/archive/2026-08-02-attack-surface-core/`
**Artifact store**: hybrid (Engram + OpenSpec filesystem)
**Delivery strategy**: chained (feature-branch-chain), 4 PR slices + remediation batch R, consolidated to `main` (`c9c1071`), deployed to www.aukalabs.com

## Cycle Outcome

| Metric | Value |
|--------|-------|
| Requirements | 10/10 PASS |
| Scenarios | 19/19 PASS |
| Tasks | 23/23 complete (0 unchecked) |
| Backend tests | 58 passed / 2 skipped (RLS PG-only) |
| Frontend tests | 42/42 (8/8 files) |
| Type-check (`tsc --noEmit`) | clean, exit 0 |
| Lint | 0 errors (7 pre-existing warnings in untouched files) |
| Verdict | PASS (strict envelope + human assessment) |
| Evidence revision | `sha256:d9e4fdef8938f2b89f045f73f9848ff4ce2dcb83938c063498cfec816ad8661d` |

## Final-State Facts (per verify-report, evidence_revision `sha256:d9e4fdef…`)

- Verification passed on re-verify after remediation batch R: 10/10 requirements, 19/19 scenarios, verdict `pass`.
- The prior verify (evidence_revision `sha256:5038f3d1…`, verdict `fail`) flagged 1 PARTIAL scenario ("Dashboard counts reflect data") and 8 pre-existing frontend test failures. Remediation batch R closed both:
  - `GET /asm/stats` backend endpoint + `api.asm.getStats()` + dashboard cards wired to real counts, covered by `TestStats` and `app/dashboard/page.test.tsx`.
  - MFA/login test failures fixed: `lib/api.ts` `auth.mfa.setup` type corrected from `uri` to `provisioning_uri` (contract drift), and `app/login/page.tsx` rewritten to consume AuthContext with the login TOTP step (the backend `/auth/login` does not yet emit `mfa_required`/`partial_token`; frontend handles the contract — backend MFA-challenge-on-login emission is out of scope, recorded as SUGGESTION).
- Full change implemented in 4 chained PR slices (PR 1 data foundation → PR 2 discovery services → PR 3 orchestration + API → PR 4 frontend wiring) plus remediation batch R; consolidated to `main` (`c9c1071`) and deployed.

## Review Gate Resolution (Maintainer-Authorized)

**MAINTAINER-AUTHORIZED DECISION**: `reviewGate.delivery: disabled/unmanaged` for this change — the kill switch is off and no native review governs this change (consistent with the 5 prior changes: `ci-pipeline`, `waitlist-api`, `docs-sync-pricing`, `mfa-auth`, `multi-tenant-rls`).

The reviewGate was `invalidated` by the merge-to-main content relationship change, NOT by any code defect. Per the Native Review Receipt Gate, `disabled/unmanaged` is the only relaxation, and it was explicitly authorized by the maintainer in the archive launch prompt. The SDD verify PASS (native `sdd-verify-validate` admitted `verdict: pass`) is the quality gate for this change.

No `review.reset` or any review transaction was attempted — this is a deliberate maintainer decision. No review artifacts exist for this change (no `reviews/` directory in the change folder, no `sdd/attack-surface-core/review/*` Engram topics), consistent with the disabled/unmanaged state.

## Spec Sync

| Domain | Action | Details |
|--------|--------|---------|
| `attack-surface` | Created (new domain) | Full spec copied verbatim from delta: `openspec/changes/attack-surface-core/specs/attack-surface/spec.md` → `openspec/specs/attack-surface/spec.md` (10 requirements, 19 scenarios). Diff verified IDENTICAL after archive move. |

`openspec/config.yaml` `rules.archive` ("Warn before merging destructive deltas") — not triggered: new-domain creation is additive, not destructive.

## Engram Traceability (Observation IDs)

| Artifact | Engram ID | Sync ID |
|----------|-----------|---------|
| proposal | #87 | obs-2d72c8f717fa6704 |
| spec | #88 | obs-2e61a5ee39e7386d |
| design | #89 | obs-39f32353e0ecd9f4 |
| tasks | #91 | obs-0ebf93ff0968c687 |
| apply-progress | #93 | obs-c661b0e0b0cc8d6e |
| verify-report | #102 | obs-1eaaf7be8f747ee8 |
| archive-report | (this report) | — |
| review/* | none | none (disabled/unmanaged per maintainer authorization) |

## Archive Verification Checklist

- [x] Main specs updated: `openspec/specs/attack-surface/spec.md` created, byte-identical to delta
- [x] Change folder moved: `openspec/changes/attack-surface-core/` → `openspec/changes/archive/2026-08-02-attack-surface-core/`
- [x] Archive contains all artifacts: proposal.md, exploration.md, specs/attack-surface/spec.md, design.md, tasks.md, apply-progress.md, verify-report.md, archive-report.md
- [x] Archived `tasks.md`: 23/23 checked, 0 unchecked implementation tasks
- [x] Active changes directory no longer contains this change

## Known Notes / Suggestions (carried from verify, non-blocking)

1. Asset model omits spec's `discovered_at` column (`first_seen`/`last_seen` cover it) — align spec text or add column in a follow-up.
2. `get_tenant_context` design shorthand resolved to existing `get_current_user` — documented deviation.
3. Discovery module path flat (`services/`) vs design's `services/discovery/` subpackage — orchestrator-directed, documented.
4. `lib/api.ts` asm method names differ from design's `list()/scan()/results()` — implemented `listAssets()/scanDomain()/getResults()/getStats()`, self-consistent with backend DTOs.
5. Scan status verb `completed` vs spec `complete` — forward-compatible with Sprint-2 queue.
6. "Campañas de phishing" dashboard card stays static `0` — no counts endpoint for that domain; out of scope.
7. Backend `/auth/login` does not yet emit `mfa_required`/`partial_token` — frontend handles contract; backend emission out of scope.

## SDD Cycle Complete

The change has been fully planned, implemented, verified, and archived. No CRITICAL or WARNING findings remain. Ready for the next change.
