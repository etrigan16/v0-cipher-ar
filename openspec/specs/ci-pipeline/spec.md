# CI Pipeline Specification

## Purpose

GitHub Actions CI workflow that validates every push and PR on main with lint, TypeScript check, unit tests, and build — and makes the `quality` check required for merge.

## Requirements

### Requirement: CI Workflow Exists

The repo MUST contain `.github/workflows/ci.yml` defining a single `quality` job on `ubuntu-latest`.

#### Scenario: Workflow file present

- GIVEN the repository root
- WHEN `.github/workflows/ci.yml` is read
- THEN the file exists and defines a `quality` job

#### Scenario: Workflow triggers on push and PR only

- GIVEN the CI workflow file
- WHEN its `on` section is inspected
- THEN it triggers on `push` to `main` and `pull_request` to `main`
- AND it does NOT use `pull_request_target`

### Requirement: CI Job Steps

The `quality` job MUST run checkout, node setup, pnpm setup, python setup, dependency install, lint, `tsc --noEmit`, vitest, pytest, and build in that order.

#### Scenario: All required steps present

- GIVEN the CI workflow file
- WHEN its job steps are listed
- THEN the job contains steps for checkout, setup-node (node 22), pnpm/action-setup (version 11), setup-python (3.12), install, lint, tsc --noEmit, vitest, pytest, and build

### Requirement: CI Action Versions

The workflow MUST use actions/checkout@v7, actions/setup-node@v7, actions/setup-python@v7, and pnpm/action-setup@v6 with `version: 11`.

#### Scenario: Correct action versions

- GIVEN the CI workflow file
- WHEN each action reference is inspected
- THEN checkout uses v7, setup-node uses v7, setup-python uses v7, and pnpm/action-setup uses v6 with version 11

### Requirement: CI Caching

The workflow MUST cache the pnpm store and pip cache between runs.

#### Scenario: Caching configured

- GIVEN the CI workflow file
- WHEN caching steps are inspected
- THEN pnpm store and pip cache are configured

### Requirement: Dummy Secret Only

The workflow MUST set a dummy `SECRET_KEY` at the job level and MUST NOT reference any real secret.

#### Scenario: No real secrets in workflow

- GIVEN the CI workflow file
- WHEN all env values are inspected
- THEN SECRET_KEY is a dummy placeholder and no real secret values are present

### Requirement: Branch Protection

The `main` branch MUST have branch protection requiring the `quality` check.

#### Scenario: Protection requires quality check

- GIVEN branch protection rules on main
- WHEN the required checks are listed
- THEN `quality` is listed as a required check

### Requirement: Minimal Permissions

The workflow MUST set `permissions: contents: read` and MUST NOT grant write or secret access.

#### Scenario: Minimal permissions configured

- GIVEN the CI workflow file
- WHEN the permissions block is inspected
- THEN `contents: read` is set and no broader permissions are granted

### Requirement: Concurrency Control

The workflow MUST cancel in-progress runs for the same branch to avoid conflicting results.

#### Scenario: Concurrency cancel-in-progress

- GIVEN the CI workflow file
- WHEN the concurrency config is inspected
- THEN `cancel-in-progress` is set
