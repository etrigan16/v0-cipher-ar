# Risk Scoring Specification

## Purpose

Deterministic, CVSS-like risk scoring over tenant findings. A rule engine generates findings from fingerprints (fixing the zero-findings gap), a pure scoring engine computes per-finding `risk_score` (0-10) and `risk_level`, and `Asset.risk_score` aggregates open findings. Exposed via findings / risk-summary / asset-detail / PATCH endpoints and dashboard charts.

## Requirements

### Requirement: R1 Finding Generation Rules

The system MUST evaluate injectable, pure rules against each asset fingerprint during a scan and persist one `Finding` per fired rule with `finding_type`, `severity`, `title`, `detail`, and scoring context. Rules MUST cover: missing security headers (HSTS, X-Content-Type-Options, CSP), TLS issues (expired/self-signed/CN mismatch), exposed non-standard ports, `Server` header version disclosure, and insecure cookie flags.

#### Scenario: Rule fires on fingerprint

- GIVEN an asset fingerprint missing the HSTS header
- WHEN the scan persists findings for that asset
- THEN a `Finding` row exists with `finding_type`, `severity`, `title`, and `detail` populated

#### Scenario: No rule matches

- GIVEN a fingerprint matching no rule
- WHEN the scan persists findings
- THEN zero findings are created for that asset and the scan completes

#### Scenario: Deterministic rules

- GIVEN the same fingerprint
- WHEN rules run twice
- THEN the identical finding set is produced without network access

### Requirement: R2 Finding Score Computation

The system MUST compute `risk_score` (Float 0-10) and derived `risk_level` for every finding from a deterministic formula: severity base (`info=0, low=2, medium=5, high=8, critical=10`) adjusted by context modifiers (exposed service/port, public TLS issues, version disclosure, missing headers). The function MUST be pure over (severity, fingerprint) — no external calls — and MUST clamp output to [0,10].

#### Scenario: Critical exposed service scores high

- GIVEN a `critical` finding on an exposed non-standard port
- WHEN the score is computed
- THEN `risk_score` is above 8 and `risk_level` is `critical`

#### Scenario: Deterministic output

- GIVEN identical (severity, fingerprint) inputs
- WHEN the score is computed twice
- THEN identical `risk_score` and `risk_level` result

#### Scenario: Clamping

- GIVEN modifiers that would exceed 10
- WHEN the score is computed
- THEN the result is clamped to exactly 10.0

### Requirement: R3 Asset Risk Aggregate

The system MUST compute `Asset.risk_score` as the max of the asset's open findings (0.0 when none) and MUST persist it after each scan and after each finding status change.

#### Scenario: Asset with findings

- GIVEN an asset with open findings scoring 3.2 and 7.5
- WHEN the aggregate is recomputed
- THEN `Asset.risk_score` is 7.5

#### Scenario: Asset without findings

- GIVEN an asset with no open findings
- WHEN the aggregate is recomputed
- THEN `Asset.risk_score` is 0.0

#### Scenario: Re-scan overwrites

- GIVEN a re-scanned asset
- WHEN the scan completes
- THEN the aggregate is recomputed from current findings (no history kept)

### Requirement: R4 Findings List Endpoint

The system MUST expose `GET /asm/findings` scoped to the authenticated tenant, supporting filters `severity`, `status`, `asset_id`, `scan_id`, sorted by `risk_score` descending, with pagination (`limit`/`offset`). Entries MUST include `risk_score`, `risk_level`, `remediation`, `status`.

#### Scenario: Tenant lists findings

- GIVEN a tenant with findings at different risk scores
- WHEN `GET /asm/findings` is called
- THEN findings are returned sorted by `risk_score` descending with risk fields populated

#### Scenario: Filter by status

- GIVEN findings with mixed statuses
- WHEN `GET /asm/findings?status=open` is called
- THEN only open findings are returned

#### Scenario: Cross-tenant isolation

- GIVEN a tenant B finding and a tenant A caller
- WHEN tenant A lists findings
- THEN tenant B's finding is absent

### Requirement: R5 Risk Summary Endpoint

The system MUST expose `GET /asm/risk-summary` returning tenant-scoped severity distribution counts, average and maximum `risk_score`, open-finding count, and top findings (default 5 by `risk_score`).

#### Scenario: Summary from real data

- GIVEN a tenant with findings
- WHEN `GET /asm/risk-summary` is called
- THEN severity counts, avg/max risk, and top findings reflect only that tenant's data

#### Scenario: Empty tenant

- GIVEN a tenant with no findings
- WHEN `GET /asm/risk-summary` is called
- THEN zero counts and an empty top-findings list are returned (200, not an error)

### Requirement: R6 Asset Detail Endpoint

The system MUST expose `GET /asm/assets/{id}` returning the asset and its findings, scoped to the tenant.

#### Scenario: Asset with findings

- GIVEN an asset belonging to the tenant
- WHEN `GET /asm/assets/{id}` is called
- THEN the asset plus its findings are returned

#### Scenario: Cross-tenant or unknown asset

- GIVEN an asset of another tenant or a nonexistent id
- WHEN the endpoint is called
- THEN 404 is returned with no data leak

### Requirement: R7 Finding Status Update

The system MUST expose `PATCH /asm/findings/{id}` accepting `{"status": "resolved"|"fp"}` over the domain `open|resolved|fp`, scoped to the tenant, and MUST recompute the owning asset's aggregate after the change.

#### Scenario: Resolve a finding

- GIVEN an open finding belonging to the tenant
- WHEN `PATCH /asm/findings/{id}` with `{"status": "resolved"}` is called
- THEN the finding's `status` is `resolved` and the asset aggregate is recomputed

#### Scenario: Invalid status rejected

- GIVEN any finding
- WHEN PATCH is called with `{"status": "wontfix"}`
- THEN 422 is returned and the status is unchanged

#### Scenario: Cross-tenant PATCH denied

- GIVEN a finding of another tenant
- WHEN PATCH is called
- THEN 404 is returned and no change is persisted
