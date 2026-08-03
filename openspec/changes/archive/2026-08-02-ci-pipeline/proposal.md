# Proposal: CI Pipeline (GitHub Actions) for v0-cipher-ar

## Intent

The repo has zero CI — no `.github/`, no workflows, no branch protection on main (verified live). Lint, `tsc --noEmit`, vitest (16), pytest (9) and build are green locally but nothing runs on GitHub, so merges ship unverified. This change puts existing gates in CI, makes `pnpm build` a real type gate, reports coverage informatively, and makes the CI check required on main. Proposal question round was answered by the user: the five binding scope decisions below.

## Scope

### In Scope
- `.github/workflows/ci.yml` (new): single `quality` job — checkout@v7 → pnpm/action-setup@v6 (`version: 11`) → setup-node@v7 (node 22, cache pnpm) → setup-python@v7 (3.12, cache pip) → install FE+BE deps → lint → `tsc --noEmit` → vitest → pytest → build. Triggers: push main + PR to main (repo branches only). `permissions: contents: read`, concurrency cancel-in-progress, dummy job-level `SECRET_KEY`.
- Type gate flip: `next.config.mjs` `ignoreBuildErrors: true → false`.
- Coverage tooling (report only, no gate): `package.json` adds `@vitest/coverage-v8`; `vitest.config.ts` coverage (v8, text); `backend/requirements.txt` adds pytest-cov.
- `package.json` adds `"packageManager": "pnpm@11.18.0"` (corepack pin).
- Merge gate: branch protection on main requires the `quality` check.
- Wiki board tracker in `wiki/projects/aukalabs/sprint-0-foundation.md` (gitignored) + pointer line: authoritative tracking lives in openspec/ + Engram + `gentle-ai sdd-status`.

### Out of Scope
Deploy-staging (dedicated follow-up); E2E Playwright; Postgres integration job; fork PR handling (`pull_request_target`); coverage hard gate (Sprint-0 DoD 70% pending); SHA-pinned actions; doc-drift fixes.

## Capabilities

- **New** `ci-pipeline`: CI validation workflow + required merge check.
- **Modified** `code-quality`: build MUST fail on TypeScript errors.
- **Modified** `test-infrastructure`: coverage tooling added, report-only.

## Approach

One job, one runner (~2-3 min for 25 tests). pnpm 11 via action `version` input; `--frozen-lockfile` auto on CI; `allowBuilds` already covers sharp/unrs-resolver. Backend tests need no Postgres (SQLite override; conftest sets SECRET_KEY; dummy env is belt-and-suspenders). `pull_request` (never `pull_request_target`) → no secrets reach forks. Branch protection set after the workflow lands so the `quality` check context exists.

## Affected Areas

| Area | Impact | Change |
|---|---|---|
| `.github/workflows/ci.yml` | New | quality job (~75 lines) |
| `next.config.mjs` | Modified | 1-line flip |
| `package.json`, `pnpm-lock.yaml` | Modified | packageManager + coverage devDep |
| `vitest.config.ts` | Modified | coverage config |
| `backend/requirements.txt` | Modified | + pytest-cov |
| wiki sprint board | Modified | tracker (gitignored) |
| main branch protection | New | require `quality` check |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Secret leak | Low | Dummy SECRET_KEY only; never RESEND_API_KEY; `pull_request` redacts secrets for forks |
| Version drift | Med | Majors pinned, verified live; node 22 / python 3.12 in YAML |
| Build gate breaks CI | Low | tsc clean today; fallback = drop flip, keep CI tsc step |
| Protection blocks merges (missing/misnamed check) | Med | Set protection after workflow lands; exact name `quality` |
| CI outage blocks merges | Low | Accepted solo-repo tradeoff |

## Rollback

Single revert commit for flip + manifest/lockfile/requirements; delete or disable ci.yml; remove required check from protection. No data migration.

## Dependencies

- Baseline merged: main `557d69c` (PRs #34/#35) — all gates green on main.
- GitHub Actions availability; repo admin rights for branch protection.
- Action majors verified live 2026-08-01.

## Success Criteria

- [ ] `quality` green on push to main and repo PRs (lint, tsc, vitest, pytest, build).
- [ ] `pnpm build` fails on a TypeScript error (flip verified).
- [ ] CI logs report FE + BE coverage %; nothing blocks on it.
- [ ] Failing `quality` blocks merge via protection.
- [ ] No real secrets in workflow.
- [ ] Wiki tracker + pointer line added.
