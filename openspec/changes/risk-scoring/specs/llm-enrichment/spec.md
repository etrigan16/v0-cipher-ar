# LLM Enrichment Specification

## Purpose

Optional-key LLM enrichment of findings via an OpenAI-compatible client pointed at Groq (ADR-005). Enrichment adds `remediation` and `context` to findings; when no key is configured or the call fails, deterministic templates are used. Output is DB-persisted; already-enriched findings are skipped (DB acts as cache; no Redis in infra).

## Requirements

### Requirement: R1 Optional Key with Template Fallback

The system MUST configure the LLM client only when `LLM_API_KEY` is set, honoring `LLM_BASE_URL` and `LLM_MODEL` overrides; when the key is absent, enrichment MUST produce deterministic fallback templates for `remediation`/`context`. A missing key or failed LLM call MUST NOT fail the scan.

#### Scenario: Key configured

- GIVEN `LLM_API_KEY` set with a Groq base URL
- WHEN enrichment runs
- THEN requests are sent to the configured endpoint

#### Scenario: Key absent

- GIVEN no `LLM_API_KEY`
- WHEN enrichment runs
- THEN findings receive template `remediation`/`context` and the scan completes

#### Scenario: LLM call failure

- GIVEN an LLM error mid-batch
- WHEN enrichment runs
- THEN affected findings fall back to templates and other findings still enrich

### Requirement: R2 Enrichment Batch and On-Demand

The system SHOULD enrich a scan's findings in a batch after scan completion and MUST expose `POST /asm/findings/{id}/enrich` for on-demand single-finding enrichment, both tenant-scoped.

#### Scenario: Batch after scan

- GIVEN a completed scan with findings
- WHEN the post-scan batch runs
- THEN each eligible finding is enriched

#### Scenario: On-demand enrich

- GIVEN a tenant finding
- WHEN `POST /asm/findings/{id}/enrich` is called
- THEN the finding is enriched and persisted

#### Scenario: Cross-tenant enrich denied

- GIVEN a finding of another tenant
- WHEN on-demand enrich is called
- THEN 404 is returned

### Requirement: R3 Persistence

The system MUST persist enrichment output (`remediation`, `context`/`llm_summary`, `enriched_at`) on the `Finding` row, whether produced by the LLM or by templates.

#### Scenario: Enriched fields stored

- GIVEN an enriched finding
- WHEN the row is read back
- THEN `remediation`, `context`, and `enriched_at` are populated

### Requirement: R4 Non-determinism Handling

The system MUST skip findings that already have `enriched_at` set (in both batch and on-demand paths) and MUST validate LLM output shape before persisting. Enrichment MUST NOT overwrite existing enrichment.

#### Scenario: Already-enriched skipped

- GIVEN a finding with `enriched_at` set
- WHEN the batch runs
- THEN it is not re-enriched and existing values are unchanged

#### Scenario: Shape validation

- GIVEN an LLM response missing required fields
- WHEN the response is processed
- THEN the finding falls back to templates or stays unenriched rather than persisting malformed data

#### Scenario: Deterministic tests

- GIVEN a mocked LLM client
- WHEN tests assert enrichment behavior
- THEN they assert shape and flow, not exact LLM content
