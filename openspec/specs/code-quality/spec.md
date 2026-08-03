# Code Quality Specification

## Purpose

Restore a working lint pipeline and apply repo hygiene quick wins so quality gates are real and enforceable.

## Requirements

### Requirement: Working Lint

The frontend MUST provide a working `lint` script backed by ESLint 9 flat config (`eslint.config.mjs`) with `eslint-config-next`, and eslint MUST be present in devDependencies.

#### Scenario: Lint passes on a clean tree

- GIVEN ESLint and its config are installed
- WHEN `pnpm lint` is run
- THEN the exit code is 0

#### Scenario: Lint fails on violations

- GIVEN a file with an ESLint violation
- WHEN `pnpm lint` is run
- THEN the exit code is non-zero and the violation is reported

### Requirement: Package Name

`package.json` MUST declare `name` as `aukalabs`.

#### Scenario: Manifest name corrected

- GIVEN the root manifest
- WHEN `package.json` is inspected
- THEN `name` equals `aukalabs`

### Requirement: Dead Stylesheet Removal

`styles/globals.css` MUST be removed, and no application file MAY import or reference it.

#### Scenario: Dead file gone

- GIVEN the repository tree
- WHEN references to `styles/globals.css` are searched
- THEN the file does not exist and no imports reference it

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
