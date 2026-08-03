# Test Infrastructure Specification

## Purpose

Working test harnesses for both stacks so future changes run RED-GREEN-REFACTOR: a vitest frontend suite, a pytest backend suite, and the strict-TDD config flip.

## Requirements

### Requirement: Frontend Test Suite

The frontend MUST provide a vitest-based test runner (React Testing Library, jsdom, user-event) with `@/*` alias support and a headless `pnpm test` script. Sample tests MUST cover pure utilities (`lib/utils.ts`), the API client with mocked fetch (`lib/api.ts`), and the auth flow (`components/auth-context.tsx`, `app/login/page.tsx`).

#### Scenario: Sample suite passes

- GIVEN frontend dependencies are installed
- WHEN `pnpm test` is run
- THEN the exit code is 0 and all sample tests pass
- AND no real network calls are made (fetch is mocked)

#### Scenario: Regression fails the suite

- GIVEN a sample test that expects behavior the code no longer provides
- WHEN `pnpm test` is run
- THEN the exit code is non-zero and the failing test is reported by name

### Requirement: Backend Test Suite

The backend MUST provide a pytest suite (pytest, pytest-asyncio, httpx) under `backend/tests/` that overrides the database dependency to run on SQLite via aiosqlite without an external Postgres. The suite MUST cover `/health` and the auth flow: register (success, duplicate email), login (success, bad credentials), and `/auth/me` (valid and invalid token).

#### Scenario: Health and auth tests pass

- GIVEN backend dependencies are installed
- WHEN `pytest` is run from `backend/`
- THEN all health and auth tests pass
- AND tests use the SQLite override, never the configured Postgres URL

#### Scenario: Duplicate registration is rejected

- GIVEN an email already registered
- WHEN register is called again with the same email
- THEN the API responds with HTTP 400

### Requirement: Strict-TDD Config Flip

After both suites exist and pass, `openspec/config.yaml` MUST set `apply.tdd: true` and non-empty `test_command` values, and the testing-capabilities cache MUST be updated to report the installed runners.

#### Scenario: Config flipped once suites are green

- GIVEN both test suites pass
- WHEN the config flip is applied
- THEN `openspec/config.yaml` records `apply.tdd: true` and the frontend/backend test commands

#### Scenario: Capabilities cache reflects the runners

- GIVEN the config flip is applied
- WHEN the testing-capabilities cache is read
- THEN it reports strict TDD enabled with vitest and pytest as available runners

### Requirement: Coverage Tooling (Report Only)

The frontend MUST use `@vitest/coverage-v8` with text reporter configured in `vitest.config.ts`. The backend MUST include `pytest-cov` in `requirements.txt`. CI MUST report FE and BE coverage percentages but MUST NOT block merges on coverage thresholds.

(Previously: no coverage tooling was installed; no coverage reporting existed)

#### Scenario: FE coverage reports in CI

- GIVEN the CI workflow runs vitest
- WHEN the vitest output is inspected
- THEN coverage percentage for FE is reported in the logs

#### Scenario: BE coverage reports in CI

- GIVEN the CI workflow runs pytest
- WHEN the pytest output is inspected
- THEN coverage percentage for BE is reported in the logs

#### Scenario: Coverage does not block merges

- GIVEN coverage is below any threshold
- WHEN the `quality` CI job runs
- THEN the job passes as long as lint, tsc, vitest, pytest, and build all pass
