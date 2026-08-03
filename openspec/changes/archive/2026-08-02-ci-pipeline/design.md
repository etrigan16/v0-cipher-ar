# Design: CI Pipeline for v0-cipher-ar

## Technical Approach

Single `quality` job on `ubuntu-latest` that runs lint, TypeScript check, unit tests, and build on every push to main and PR to main. The design maps directly to the proposal's approach and satisfies all specs in `ci-pipeline/spec.md`, `code-quality/spec.md`, and `test-infrastructure/spec.md`.

## Architecture Decisions

### Decision: Single job, one runner

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Single `quality` job | Simpler to maintain; ~2-3 min runtime for 25 tests | **Chosen** |
| Split jobs (lint/tsc/test/build) | Parallelism but more YAML, more maintenance | Rejected — overkill for 25 tests |

### Decision: Action major-version pinning

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Pin majors (checkout@v7, setup-node@v7, setup-python@v7, pnpm/action-setup@v6) | Balances stability with minor/patch updates | **Chosen** |
| SHA pinning | Maximum reproducibility but breaks on action repo deletes | Rejected — maintenance burden |
| Floating tags (`@latest`) | Always current but unpredictable breakage | Rejected — no reproducibility |

### Decision: `pnpm/action-setup@v6` with explicit `version: 11`

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Explicit `version: 11` input | Required because `package.json` lacks `packageManager` field; corepack needs the pin | **Chosen** |
| Omit version, rely on `packageManager` | Would fail — field is absent | Rejected |

### Decision: Dummy `SECRET_KEY` at job level

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Dummy value at job env | Belt-and-suspenders; backend config requires it, CI has no real secret | **Chosen** |
| Omit SECRET_KEY entirely | Backend `Settings` has no default — `pnpm build` would fail | Rejected |
| Use real secret from repo | Never; `pull_request` redacts secrets for forks anyway | Rejected — unnecessary risk |

### Decision: Wiki board tracker (gitignored)

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Local gitignored file + pointer line | Zero review cost, no external service | **Chosen** |
| GitHub Projects | Requires repo settings, external dependency | Rejected — out of scope |

## Data Flow

```
push to main / PR to main
  │
  ▼
.github/workflows/ci.yml (quality job)
  │
  ├─ checkout@v7
  ├─ setup-node@v7 (node 22, cache pnpm)
  ├─ pnpm/action-setup@v6 (version 11)
  ├─ setup-python@v7 (3.12, cache pip)
  ├─ pnpm install --frozen-lockfile
  ├─ pnpm lint
  ├─ npx tsc --noEmit
  ├─ pnpm test (vitest → coverage v8 text)
  ├─ pytest (pytest-cov → text)
  └─ pnpm build (next build; fails on TS errors)
  │
  ▼
quality check result → branch protection on main
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `.github/workflows/ci.yml` | Create | Single `quality` job with all steps, caching, dummy SECRET_KEY |
| `next.config.mjs` | Modify | `ignoreBuildErrors: true → false` (type gate flip) |
| `package.json` | Modify | Add `@vitest/coverage-v8` devDep; add `packageManager: "pnpm@11.18.0"` |
| `vitest.config.ts` | Modify | Add coverage config (v8, text reporter) |
| `backend/requirements.txt` | Modify | Add `pytest-cov` |
| `wiki/projects/aukalabs/sprint-0-foundation.md` | Modify | Add CI tracker section |
| `.gitignore` | Modify | No change needed — wiki already gitignored |

## Interfaces / Contracts

No new interfaces or API contracts. The CI workflow exposes a single check name `quality` that branch protection requires.

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | CI YAML syntax | Validate with `actionlint` or manual review |
| Integration | End-to-end workflow run | Push to main, verify `quality` check passes |
| E2E | Branch protection enforcement | Attempt merge without `quality` green; verify blocked |

## Threat Matrix

| Boundary | Minimum adversarial cases | Applicability | Design response | Planned RED tests |
|---|---|---|---|---|
| PR commands | `pull_request` vs `pull_request_target` | Applicable | Workflow uses `pull_request` only; no `pull_request_target` — secrets never reach forks | Verify `on.pull_request` not `pull_request_target` in ci.yml |
| Git repository selection | Relative paths, cwd authority | Applicable | CI runs on `ubuntu-latest` with explicit `working-directory` not needed (default is repo root) | Verify steps run from repo root |
| Commit state | Staged changes, clean tree | Applicable | `tsc --noEmit` checks all tracked files; build fails on errors | Verify `pnpm build` fails on a TS error after flip |
| Push state | First push to main, force push | Applicable | `push` trigger on `main` covers all push events | Verify workflow fires on push to main |
| PR commands | Explicit `--head`, environment prefix | Applicable | `pull_request` trigger provides `github.event.pull_request` context; no `--head` needed | Verify PR trigger fires on PRs to main |

## Migration / Rollout

No migration required. Rollback per component:

- **CI workflow**: Delete `.github/workflows/ci.yml` and remove `quality` from branch protection.
- **Type gate flip**: Revert `next.config.mjs` line to `ignoreBuildErrors: true`.
- **Coverage tooling**: Remove `@vitest/coverage-v8` from devDeps, remove coverage config from `vitest.config.ts`, remove `pytest-cov` from `requirements.txt`.
- **Branch protection**: Remove required check via GitHub Settings → Branches.
- **Wiki tracker**: Remove tracker section from `sprint-0-foundation.md`.

All rollbacks are single-revert commits or direct file deletions — no data migration needed.

## Open Questions

- [ ] Whether `pnpm install --frozen-lockfile` is needed explicitly (pnpm action may do this by default with `version: 11`).
- [ ] Exact branch protection UI steps (GitHub Settings → Branches → Add rule) — manual, not automatable via workflow.
