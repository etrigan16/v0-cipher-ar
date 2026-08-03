# Tasks: CI Pipeline

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~85-105 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | single PR |
| Delivery strategy | ask-on-risk |
| Chain strategy | stacked-to-main |
| Decision needed before apply | Yes |

Decision needed before apply: Yes
Chained PRs recommended: No
Chain strategy: stacked-to-main
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | CI workflow + type gate + coverage tooling | PR 1 | `pnpm lint && npx tsc --noEmit && pnpm test -- --coverage && pnpm build` | push to main / PR to main | Revert ci.yml + next.config.mjs + package.json + vitest.config.ts + requirements.txt |

## Phase 1: Foundation (config & tooling)

- [x] 1.1 Add `"packageManager": "pnpm@11.18.0"` to `package.json`
- [x] 1.2 Add `@vitest/coverage-v8` to `devDependencies` in `package.json`
- [x] 1.3 Add `pytest-cov` to `backend/requirements.txt`
- [x] 1.4 Add coverage config (v8, text reporter) to `vitest.config.ts`

## Phase 2: CI Workflow & Type Gate

- [x] 2.1 Create `.github/workflows/ci.yml` with single `quality` job (checkout@v7, setup-node@v7 node 22, pnpm/action-setup@v6 version 11, setup-python@v7 3.12, install, lint, tsc --noEmit, vitest, pytest, build; caching pnpm + pip; dummy SECRET_KEY; `pull_request` trigger; `permissions: contents: read`; concurrency cancel-in-progress)
- [x] 2.2 Flip `ignoreBuildErrors: true → false` in `next.config.mjs`

## Phase 3: Lockfile & Verification

- [x] 3.1 Run `pnpm install` to update `pnpm-lock.yaml` and `node_modules`
- [x] 3.2 Verify CI YAML syntax and all required steps present in `ci.yml`
- [x] 3.3 Verify `tsc --noEmit` passes with the type gate flip applied
- [x] 3.4 Verify vitest and pytest coverage reporting works locally

## Phase 4: Protection & Tracking

- [x] 4.1 Set branch protection on `main` requiring the `quality` check (GitHub Settings → Branches → Add rule)
- [x] 4.2 Add CI tracker section to `wiki/projects/aukalabs/sprint-0-foundation.md` (gitignored, local-only)
