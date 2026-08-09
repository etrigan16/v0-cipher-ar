# Phishing Campaigns Specification

## Purpose

Tenant-owned campaign orchestration: Campaign and Target models, campaign CRUD, CSV target upload, launch (per-target unique tracking tokens, status `active`), and cancel. Delivery is links-only per the consent model — the system MUST NOT send emails; the tenant distributes links.

## Requirements

### Requirement: R1 Campaign Model

The system MUST persist `Campaign` rows with `tenant_id` (FK), `name`, `template_id` (FK), and `status` in `draft|active|completed|cancelled`, following repo model conventions with RLS enabled.

#### Scenario: Create draft campaign

- GIVEN an authenticated tenant
- WHEN a campaign is created with a name and a template the tenant owns
- THEN a Campaign row persists with status `draft`

#### Scenario: Invalid status rejected

- GIVEN any campaign
- WHEN an update sets a status outside the domain
- THEN 422 is returned and the status is unchanged

### Requirement: R2 Campaign CRUD and CSV Upload

The system MUST expose tenant-scoped `GET/POST /phishing/campaigns`, `GET/PUT/DELETE /phishing/campaigns/{id}`, and `POST /phishing/targets/upload` accepting CSV (email, name). Malformed CSV MUST be rejected with 422 and no partial persistence.

#### Scenario: Create and list campaign

- GIVEN an authenticated tenant
- WHEN a campaign is created
- THEN it appears in `GET /phishing/campaigns` for that tenant only

#### Scenario: Valid CSV upload

- GIVEN a draft campaign
- WHEN a CSV with valid email,name rows is uploaded
- THEN one Target is created per row, linked to the campaign, status `pending`

#### Scenario: Invalid CSV rejected

- GIVEN a draft campaign
- WHEN a CSV with a row missing email or with an invalid email format is uploaded
- THEN 422 is returned and no targets are persisted

### Requirement: R3 Target Model

The system MUST persist `Target` rows with `tenant_id` (FK), `campaign_id` (FK), `email`, `name`, `status`, and a unique indexed `tracking_token`. Within one campaign, emails MUST be unique.

#### Scenario: Upload creates targets

- GIVEN a valid CSV upload
- THEN targets persist with tenant_id and campaign_id set and status `pending`

#### Scenario: Duplicate email in campaign

- GIVEN two CSV rows with the same email in one campaign
- WHEN the upload is processed
- THEN 422 is returned and no duplicate targets are created

### Requirement: R4 Launch Campaign

The system MUST, on `POST /phishing/campaigns/{id}/launch`, generate a unique `tracking_token` per target, set status `active` and `started_at`, and return per-target distributable links. Only `draft` campaigns MAY be launched; launch MUST NOT send emails.

#### Scenario: Launch draft campaign

- GIVEN a draft campaign with targets
- WHEN launch is called
- THEN every target gets a unique tracking token, status becomes `active`, and links are returned

#### Scenario: Token uniqueness

- GIVEN a campaign with N targets
- WHEN launch runs
- THEN N distinct tracking tokens exist

#### Scenario: Launch non-draft campaign

- GIVEN a campaign that is active, completed, or cancelled
- WHEN launch is called
- THEN 409 is returned and no tokens are regenerated

### Requirement: R5 Cancel Campaign

The system MUST, on `POST /phishing/campaigns/{id}/cancel`, set status `cancelled` and `completed_at`. Only `draft` or `active` campaigns MAY be cancelled; tracking tokens of a cancelled campaign MUST stop resolving.

#### Scenario: Cancel active campaign

- GIVEN an active campaign
- WHEN cancel is called
- THEN status becomes `cancelled` and tracking links stop resolving

#### Scenario: Cancel completed campaign

- GIVEN a completed campaign
- WHEN cancel is called
- THEN 409 is returned and status stays `completed`

### Requirement: R6 Tenant Scoping

All campaign and target endpoints MUST filter on the authenticated tenant's `tenant_id`; cross-tenant or unknown campaign ids MUST return 404.

#### Scenario: Cross-tenant campaign access

- GIVEN a campaign belonging to tenant B
- WHEN tenant A requests it
- THEN 404 is returned with no data leak
