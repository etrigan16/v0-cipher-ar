# Delta for Code Quality

## ADDED Requirements

### Requirement: TypeScript Build Gate

The build MUST fail on TypeScript errors. `next.config.mjs` MUST set `typescript.ignoreBuildErrors` to `false`, and the CI `quality` job MUST run `tsc --noEmit`.

(Previously: `ignoreBuildErrors` was unconstrained; CI had no TypeScript check)

#### Scenario: Build fails on TypeScript error

- GIVEN a TypeScript error exists in the codebase
- WHEN `pnpm build` is run
- THEN the exit code is non-zero and the error is reported

#### Scenario: CI tsc step catches errors

- GIVEN a TypeScript error exists in the codebase
- WHEN the `quality` CI job runs `tsc --noEmit`
- THEN the job fails and the error is reported

#### Scenario: Clean tree passes build

- GIVEN no TypeScript errors exist
- WHEN `pnpm build` is run
- THEN the exit code is 0
