# Attack Surface Specification

## Purpose

The attack-surface capability discovers, fingerprints, and persists a tenant's external attack surface. Sprint 1 core: passive (crt.sh) subdomain enumeration plus active DNS/HTTP/TLS fingerprinting, persisted into `Asset`, `Scan`, `Finding` models, tenant-isolated via RLS + app filter, exposed through the `/asm` API and wired into the attack-surface and dashboard pages.

## Requirements

### Requirement: Asset Model

The system MUST persist a discovered entity per tenant in an `Asset` model with columns: `id` (UUID via `CoercingUuid`), `tenant_id` (FK NOT NULL), `domain`, `subdomain`, `ip`, `port`, `service`, `fingerprint` (JSON), `status`, `first_seen`, `last_seen`, `discovered_at`.

#### Scenario: Asset created for discovered host

- GIVEN a scan discovers a hostname with an A record and an HTTP title
- WHEN the host is persisted
- THEN an `Asset` row exists for the tenant with `domain`, `subdomain`, `ip`, `port`, `service`, and `fingerprint` populated

#### Scenario: Re-scan upserts instead of duplicating

- GIVEN an `Asset` already exists for a subdomain with `last_seen` set
- WHEN the same subdomain is discovered again
- THEN the existing row is updated (new `last_seen`), preserving `first_seen`, and NO duplicate row is inserted

### Requirement: Scan Model

The system MUST persist discovery runs in a `Scan` model with `id`, `tenant_id` (FK), `domain`, `status` (`queued|running|complete|error`), `started_at`, `completed_at`.

#### Scenario: Scan lifecycle to complete

- GIVEN a `POST /asm/scans` with a valid domain
- WHEN discovery runs and persists assets
- THEN a `Scan` row exists with status `complete`, `started_at` set, and `completed_at` after start

#### Scenario: Scan errors recorded

- GIVEN discovery fails for a domain
- WHEN the run terminates
- THEN the `Scan` status is `error` and `completed_at` is set

### Requirement: Finding Model

The system MUST persist issues on assets in a `Finding` model with `id`, `tenant_id` (FK), `asset_id` (FK), `scan_id` (FK), `severity`, `title`, `detail`, `discovered_at`.

#### Scenario: Finding linked to asset and scan

- GIVEN a scan and an asset it created
- WHEN a fingerprinting issue is detected
- THEN a `Finding` row references that `asset_id` and `scan_id` with severity, title, and detail

### Requirement: Trigger Scan

The system MUST expose `POST /asm/scans` taking `{domain}`, run passive + active discovery synchronously, persist `Asset`/`Scan`, upsert assets, and return the scan with its assets, scoped to the authenticated tenant.

#### Scenario: Valid domain scan

- GIVEN an authenticated tenant with a valid domain
- WHEN `POST /asm/scans` is called
- THEN discovery runs, assets are persisted, and the response contains a `complete` scan and its assets

#### Scenario: Unauthenticated request rejected

- GIVEN no valid token
- WHEN `POST /asm/scans` is called
- THEN a 401 is returned and no `Scan` row is created

### Requirement: List Assets

The system MUST expose `GET /asm/assets` returning only assets of the current tenant.

#### Scenario: Tenant sees own assets

- GIVEN a tenant with persisted assets
- WHEN `GET /asm/assets` is called
- THEN the response lists only that tenant's assets, in no cross-tenant rows

#### Scenario: Another tenant isolated

- GIVEN two tenants with disjoint assets
- WHEN tenant A calls `GET /asm/assets`
- THEN tenant A sees none of tenant B's assets

### Requirement: Scan Results

The system MUST expose `GET /asm/results/{scan_id}` returning the scan and its findings, scoped to the tenant.

#### Scenario: Results returned

- GIVEN a `complete` scan belonging to the tenant
- WHEN `GET /asm/results/{scan_id}` is called
- THEN the response contains the scan and its findings

#### Scenario: Cross-tenant scan denied

- GIVEN a scan belonging to another tenant
- WHEN `GET /asm/results/{scan_id}` is called
- THEN a 404 is returned and no findings leak

### Requirement: Subdomain Enumeration (crt.sh)

The system MUST perform passive subdomain enumeration by querying crt.sh CT logs (`?q=%25.{domain}&output=json`), deduplicate hostnames, and tolerate source failure as partial.

#### Scenario: crt.sh returns subdomains

- GIVEN the crt.sh API responds with cert JSON
- WHEN enumeration runs
- THEN discovered hostnames are deduplicated and forwarded to resolution

#### Scenario: crt.sh unavailable

- GIVEN the crt.sh request times out or errors
- WHEN enumeration runs
- THEN the scan continues (partial), logging the failure rather than aborting

### Requirement: Active Fingerprinting

The system MUST resolve subdomains via dnspython (A/AAAA/CNAME) and fingerprint live hosts via httpx (status, `server`, title, `x-powered-by`) and TLS (subject/issuer), over a common-port set.

#### Scenario: Host resolved and fingerprinted

- GIVEN a hostname with a live HTTP endpoint
- WHEN active discovery runs
- THEN the host's `ip`, port, service, and HTTP/TLS fingerprint are persisted on the `Asset`

#### Scenario: Unresolvable host skipped

- GIVEN a hostname with no DNS record
- WHEN active discovery runs
- THEN no `Asset` row is created for it and the scan completes

### Requirement: Multi-tenant RLS

The system MUST enable Row-Level Security and `tenant_isolation` policies on `assets`, `scans`, and `findings` tables in PostgreSQL, and MUST apply an app-level tenant filter in routes so SQLite tests prove isolation.

#### Scenario: RLS enabled on new tables

- GIVEN PostgreSQL is the database
- WHEN the migration/init runs
- THEN RLS is ENABLED with a `tenant_isolation` policy on each new table

#### Scenario: App filter proves isolation on SQLite

- GIVEN the SQLite test fixture and two tenants
- WHEN queries run per tenant injection
- THEN each tenant only sees its own rows

### Requirement: Frontend Dashboard

The system MUST display the tenant's real assets on the attack-surface page and real asset/finding/scan counts on the dashboard, fetched via the typed `asm` API client.

#### Scenario: Attack-surface shows real assets

- GIVEN a tenant with assets
- WHEN the attack-surface page loads
- THEN it lists the real assets and supports starting a scan

#### Scenario: Dashboard counts reflect data

- GIVEN a tenant with persisted assets and scans
- WHEN the dashboard loads
- THEN the asset, finding, and scan cards show the real counts instead of zeros
