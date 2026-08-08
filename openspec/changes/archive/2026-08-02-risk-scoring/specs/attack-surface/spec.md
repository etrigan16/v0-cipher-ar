# Delta for Attack Surface

## MODIFIED Requirements

### Requirement: Finding Model

The system MUST persist issues on assets in a `Finding` model with `id`, `tenant_id` (FK), `asset_id` (FK), `scan_id` (FK), `severity`, `title`, `detail`, `discovered_at`, plus the nullable risk/enrichment columns added by migration 004: `risk_score` (Float), `risk_level`, `finding_type`, `remediation` (Text), `status` (default `open`), `context`/`llm_summary` (Text), `enriched_at` (DateTime).
(Previously: Finding had no score, remediation, status, or enrichment columns.)

#### Scenario: Finding linked to asset and scan

- GIVEN a scan and an asset it created
- WHEN a fingerprinting issue is detected
- THEN a `Finding` row references that `asset_id` and `scan_id` with severity, title, and detail

#### Scenario: New columns default safely

- GIVEN a finding persisted before risk scoring exists
- WHEN the row is read after migration 004
- THEN `risk_score`/`remediation` are NULL, `status` is `open`, and `enriched_at` is NULL without a backfill

### Requirement: Asset Model

The system MUST persist a discovered entity per tenant in an `Asset` model with columns: `id` (UUID via `CoercingUuid`), `tenant_id` (FK NOT NULL), `domain`, `subdomain`, `ip`, `port`, `service`, `fingerprint` (JSON), `status`, `first_seen`, `last_seen`, `discovered_at`, plus nullable `risk_score` (Float) aggregate added by migration 004.
(Previously: Asset had no `risk_score` column.)

#### Scenario: Asset created for discovered host

- GIVEN a scan discovers a hostname with an A record and an HTTP title
- WHEN the host is persisted
- THEN an `Asset` row exists for the tenant with `domain`, `subdomain`, `ip`, `port`, `service`, and `fingerprint` populated

#### Scenario: Re-scan upserts instead of duplicating

- GIVEN an `Asset` already exists for a subdomain with `last_seen` set
- WHEN the same subdomain is discovered again
- THEN the existing row is updated (new `last_seen`), preserving `first_seen`, and NO duplicate row is inserted

#### Scenario: risk_score nullable on legacy rows

- GIVEN assets persisted before migration 004
- WHEN the migration applies
- THEN `risk_score` is NULL until the next scan recomputes it

## ADDED Requirements

### Requirement: Additive Risk Scoring Migration 004

The system MUST ship an additive Alembic migration (004) adding the nullable Finding columns and `Asset.risk_score`; downgrade MUST drop only those columns.

#### Scenario: Upgrade on existing data

- GIVEN a populated database at migration 003
- WHEN migration 004 applies
- THEN all new columns are nullable and existing rows are untouched

#### Scenario: Downgrade

- GIVEN migration 004 applied
- WHEN it is downgraded
- THEN only the added columns are dropped and prior data remains

### Requirement: Stats Risk Fields

The system MUST extend `GET /asm/stats` with tenant-scoped risk fields — severity distribution counts, average/max `risk_score`, and open-finding count — while keeping existing `assets`/`findings`/`scans` counts unchanged.

#### Scenario: Stats include risk fields

- GIVEN a tenant with scored findings
- WHEN `GET /asm/stats` is called
- THEN existing counts plus risk fields are returned

#### Scenario: Backward compatible

- GIVEN a client reading only `assets`/`findings`/`scans`
- WHEN stats is called
- THEN the existing fields keep their shape and values
