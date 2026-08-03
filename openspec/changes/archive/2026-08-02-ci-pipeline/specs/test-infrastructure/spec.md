# Delta for Test Infrastructure

## ADDED Requirements

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
