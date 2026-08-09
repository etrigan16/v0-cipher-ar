# Phishing Results Specification

## Purpose

Tenant-scoped campaign results: per-target stats, aggregate summary with rates, PDF export reusing the reportlab generator, and a frontend results page.

## Requirements

### Requirement: R1 Per-Target Results

The system MUST expose `GET /phishing/campaigns/{id}/results` returning per-target rows with email, name, status, and per-type activity (opened/clicked/reported/credential), scoped to the tenant.

#### Scenario: Results with mixed activity

- GIVEN a campaign whose targets have varying open/click/credential Events
- WHEN results are fetched
- THEN each target row reflects its own activity

#### Scenario: Cross-tenant results

- GIVEN a campaign of tenant B
- WHEN tenant A fetches its results
- THEN 404 is returned

### Requirement: R2 Results Summary

The system MUST expose `GET /phishing/results-summary` returning aggregate counts (sent/opened/clicked/reported/credentials) and rates (open %, click %, credential %) computed from target status and Events.

#### Scenario: Summary from real data

- GIVEN a tenant with campaigns and tracking activity
- WHEN the summary is fetched
- THEN counts and rates reflect only that tenant's data

#### Scenario: Empty tenant

- GIVEN a tenant with no campaign activity
- WHEN the summary is fetched
- THEN zero counts and 0% rates are returned (200, not an error)

### Requirement: R3 PDF Export

The system MUST expose `GET /phishing/campaigns/{id}/report` returning a valid PDF via the existing reportlab generator, containing the campaign summary and per-target table, scoped to the tenant.

#### Scenario: PDF with data

- GIVEN a campaign with results
- WHEN the report is requested
- THEN bytes starting with `%PDF` are returned containing summary and per-target table

#### Scenario: Empty campaign PDF

- GIVEN a campaign with no events
- WHEN the report is requested
- THEN a valid PDF with zeroed metrics is produced

### Requirement: R4 Frontend Results Page

The frontend MUST render a campaign results page with aggregate cards (sent/opened/clicked/credentials + rates) and a per-target table fed by `api.phishing`, plus a PDF download action.

#### Scenario: Results page renders

- GIVEN a campaign with data
- WHEN the results page loads
- THEN aggregate cards and the per-target table show the fetched data

#### Scenario: Empty state

- GIVEN a campaign with no activity
- WHEN the results page loads
- THEN zeroed cards and an empty table render without errors
