# Wiki ADRs Specification

## Purpose

Define the ADR content updates for `wiki/projects/aukalabs/tech-decisions.md`: marking stale unimplemented architecture decisions as superseded or deferred, and updating the Sprint 0 CI tracker.

## Requirements

### Requirement: ADR-002 Supersession

ADR-002 (React 18 + Vite) SHALL be marked as superseded by the actual stack (Next.js 16 + React 19).

#### Scenario: ADR-002 annotated as superseded

- GIVEN the `wiki/projects/aukalabs/tech-decisions.md` file
- WHEN the ADR-002 entry is read
- THEN it contains a "Status: Superseded" annotation
- AND it references "Next.js 16 + React 19" as the superseding decision
- AND the original ADR-002 content is preserved (not deleted)

### Requirement: ADR-007 Supersession

ADR-007 (Docker → Render/Fly.io deployment) SHALL be marked as superseded by the actual deploy target (Vercel).

#### Scenario: ADR-007 annotated as superseded

- GIVEN the `wiki/projects/aukalabs/tech-decisions.md` file
- WHEN the ADR-007 entry is read
- THEN it contains a "Status: Superseded" annotation
- AND it references "Vercel deploy" as the superseding approach
- AND the original ADR-007 content is preserved (not deleted)

### Requirement: Unimplemented ADRs Deferred

Any ADR entry in `tech-decisions.md` that describes planned intent with no code implementation SHALL be annotated with "Status: Deferred" rather than "Status: Active".

#### Scenario: Unimplemented ADRs marked deferred

- GIVEN the `wiki/projects/aukalabs/tech-decisions.md` file
- WHEN entries with no corresponding code implementation are inspected
- THEN each such entry contains a "Status: Deferred" annotation

### Requirement: Sprint 0 CI Tracker

The Sprint 0 CI tracker in `wiki/projects/aukalabs/sprint-0-foundation.md` SHALL be updated from "Pending" to "Done".

#### Scenario: CI tracker completion

- GIVEN the `wiki/projects/aukalabs/sprint-0-foundation.md` file
- WHEN the CI tracker entry is read
- THEN the CI workflow status shows "Done" or "Completado"
- AND it references the GitHub Actions `quality` workflow by name
