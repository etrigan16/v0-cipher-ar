# README Content Specification

## Purpose

Define the README.md content requirements: accurate stack versions, CI presence, test commands, environment setup, and quick-start instructions for developer onboarding.

## Requirements

### Requirement: Stack Line Accuracy

The README SHALL list the actual project stack and versions as deployed.

#### Scenario: Stack versions match reality

- GIVEN the README.md file
- WHEN the stack line is read
- THEN "Next.js" appears with version 16.x
- AND "React" appears with version 19.x
- AND "FastAPI" appears
- AND "PostgreSQL" appears
- AND no reference to Next.js 14 or React 18 exists

### Requirement: CI Badge

The README SHALL display a CI status badge pointing to the GitHub Actions `quality` workflow.

#### Scenario: CI badge present

- GIVEN the README.md file
- WHEN it is scanned for markdown image links
- THEN a badge referencing `github/actions/workflows/ci.yml` or `quality` workflow is present

### Requirement: Test Commands

The README SHALL document how to run frontend tests, backend tests, lint, and type checks.

#### Scenario: Frontend test command documented

- GIVEN the README.md file
- WHEN the testing section is read
- THEN it includes `pnpm test` for frontend (vitest) tests

#### Scenario: Backend test command documented

- GIVEN the README.md file
- WHEN the testing section is read
- THEN it includes `cd backend && pytest` for backend tests

### Requirement: Environment Setup

The README SHALL include instructions for environment variable configuration referencing `backend/.env.example`.

#### Scenario: Env setup section

- GIVEN the README.md file
- WHEN the environment setup section is read
- THEN it references `backend/.env.example`
- AND it notes that a real `RESEND_API_KEY` is required for contact functionality

### Requirement: Quick Start Section

The README SHALL include a quick-start section with commands to clone, install dependencies, configure env, and run the project locally.

#### Scenario: Quick start commands present

- GIVEN the README.md file
- WHEN the quick-start section is read
- THEN it includes `pnpm install` (or equivalent install command)
- AND it includes `docker-compose up` or equivalent backend start command
