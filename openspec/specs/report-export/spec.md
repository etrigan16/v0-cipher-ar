# Report Export Specification

## Purpose

Backend-generated executive reports for a tenant: CSV via the Python stdlib and PDF via reportlab (pure-Python, slim-Docker-safe). Exposed through `GET /asm/export?format=csv|pdf`, tenant-scoped, backing the Free plan's "resumen PDF" feature.

## Requirements

### Requirement: R1 CSV Export

The system MUST generate CSV with the stdlib `csv` module from the tenant's findings, with headers: asset, finding title, severity, risk_score, status, remediation, discovered_at.

#### Scenario: CSV from tenant findings

- GIVEN a tenant with findings
- WHEN CSV export runs
- THEN valid UTF-8 CSV bytes with headers and one row per finding are produced

#### Scenario: Empty tenant

- GIVEN a tenant with no findings
- WHEN CSV export runs
- THEN CSV with headers only is produced (no error)

### Requirement: R2 PDF Export

The system MUST generate a valid PDF with reportlab containing: tenant/domain summary, severity distribution, average and maximum risk, and top findings with remediation.

#### Scenario: PDF with real data

- GIVEN a tenant with findings
- WHEN PDF export runs
- THEN bytes starting with `%PDF` are produced containing summary, distribution, and top findings

#### Scenario: Empty tenant

- GIVEN a tenant with no findings
- WHEN PDF export runs
- THEN a valid PDF with zeroed metrics is produced

### Requirement: R3 Export Endpoint

The system MUST expose `GET /asm/export?format=csv|pdf` returning the file with correct `Content-Type` and `Content-Disposition`; invalid or missing format MUST return 400; unauthenticated requests MUST return 401.

#### Scenario: CSV download

- GIVEN `format=csv`
- WHEN `GET /asm/export` is called
- THEN `text/csv` with attachment disposition is returned

#### Scenario: PDF download

- GIVEN `format=pdf`
- WHEN `GET /asm/export` is called
- THEN `application/pdf` with attachment disposition is returned

#### Scenario: Invalid format

- GIVEN `format=docx`
- WHEN `GET /asm/export` is called
- THEN 400 is returned

### Requirement: R4 Tenant Scoping

All export content MUST be filtered on the authenticated tenant's `tenant_id`; no cross-tenant data may appear in any format.

#### Scenario: Tenant-scoped content

- GIVEN tenants A and B with disjoint findings
- WHEN tenant A exports
- THEN the report contains only tenant A's findings and metrics
