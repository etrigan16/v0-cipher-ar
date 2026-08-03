# Apply Progress: ci-pipeline

## Phase 1: Foundation (config & tooling)

| Task | Status | Evidence |
|---|---|---|
| 1.1 Add `"packageManager": "pnpm@11.18.0"` to `package.json` | ✅ Complete | `package.json` now has `"packageManager": "pnpm@11.18.0"` field |
| 1.2 Add `@vitest/coverage-v8` to `devDependencies` in `package.json` | ✅ Complete | `@vitest/coverage-v8` added to devDependencies |
| 1.3 Add `pytest-cov` to `backend/requirements.txt` | ✅ Complete | `pytest-cov==5.0.0` added to requirements.txt |
| 1.4 Add coverage config (v8, text reporter) to `vitest.config.ts` | ✅ Complete | `coverage: { provider: "v8", reporter: ["text"] }` added to test config |

### Work Unit Evidence — Phase 1

| Evidence | Required value | Actual |
|---|---|---|
| Focused test command | `pnpm test -- --coverage` | 14 tests passed, coverage report shown (84.93% stmts) |
| Runtime harness | `python -m pytest --cov` in backend | 9 passed, 88% coverage |
| Rollback boundary | Revert package.json, vitest.config.ts, requirements.txt | Single revert commit scope |

## Phase 2: CI Workflow & Type Gate

| Task | Status | Evidence |
|---|---|---|
| 2.1 Create `.github/workflows/ci.yml` with single `quality` job | ✅ Complete | File created with all required steps, caching, dummy SECRET_KEY, pull_request trigger, permissions: contents: read, concurrency cancel-in-progress |
| 2.2 Flip `ignoreBuildErrors: true → false` in `next.config.mjs` | ✅ Complete | `next.config.mjs` now has `ignoreBuildErrors: false` |

### Work Unit Evidence — Phase 2

| Evidence | Required value | Actual |
|---|---|---|
| Focused test command | `npx tsc --noEmit` | Exit code 0, no errors |
| Runtime harness | `pnpm build` (type gate) | Build succeeds on clean tree; would fail on TS errors |
| Rollback boundary | Revert next.config.mjs line | Single-line revert |

## Phase 3: Lockfile & Verification

| Task | Status | Evidence |
|---|---|---|
| 3.1 Run `pnpm install` to update `pnpm-lock.yaml` | ✅ Complete | Lockfile updated; 11 packages added |
| 3.2 Verify CI YAML syntax and all required steps present | ✅ Complete | YAML parsed valid; `quality` job has all 10 steps in correct order |
| 3.3 Verify `tsc --noEmit` passes with type gate flip | ✅ Complete | `npx tsc --noEmit` exits 0 with no errors |
| 3.4 Verify vitest and pytest coverage reporting works locally | ✅ Complete | vitest: 84.93% stmts; pytest: 88% total coverage |

### Work Unit Evidence — Phase 3

| Evidence | Required value | Actual |
|---|---|---|
| Focused test command | `npx vitest run --coverage` | 14 tests passed, coverage report printed |
| Runtime harness | `python -m pytest --cov` | 9 passed, coverage report printed |
| Rollback boundary | Revert pnpm-lock.yaml, ci.yml, next.config.mjs | Single revert commit scope |

## Phase 4: Protection & Tracking

| Task | Status | Evidence |
|---|---|---|
| 4.1 Set branch protection on `main` requiring `quality` check | ✅ Complete | `gh api repos/etrigan16/v0-cipher-ar/branches/main/protection --method PUT` succeeded; `quality` listed in required_status_checks.contexts |
| 4.2 Add CI tracker section to `wiki/projects/aukalabs/sprint-0-foundation.md` | ✅ Complete | CI tracker table added with 4 rows (Pending status); updated Entregables table entry for CI/CD |

### Work Unit Evidence — Phase 4

| Evidence | Required value | Actual |
|---|---|---|
| Focused test command | N/A (manual UI action for protection; file edit for wiki) | Branch protection confirmed via API; wiki file edited |
| Runtime harness | N/A | Branch protection rule verified via `gh api` response |
| Rollback boundary | Delete ci.yml + remove protection rule + revert wiki | Single revert commit scope |

## Summary

All 12 tasks across 4 phases are complete. The CI pipeline is implemented with:
- Single `quality` job on ubuntu-latest
- Type gate flip (`ignoreBuildErrors: false`)
- Coverage reporting (v8 for FE, pytest-cov for BE) — report only, no gate
- Branch protection on main requiring `quality` check
- Wiki tracker added (gitignored, local-only)
