# Delta for Waitlist

## MODIFIED Requirements

### R1: Waitlist Model and Storage

The system MUST persist waitlist entries with email (required, unique), company (optional), `created_at` timestamp, `source` defaulting to `"landing"`, and `tenant_id` (UUID FK to tenants, nullable for migration compatibility).
(Previously: No tenant_id field)

| Field      | Type         | Required | Unique | Default |
|------------|--------------|----------|--------|---------|
| email      | str          | Yes      | Yes    | —       |
| company    | str          | No       | No     | —       |
| created_at | datetime     | Yes      | No     | now()   |
| source     | str          | Yes      | No     | "landing" |
| tenant_id  | UUID FK      | No (null) | No    | —       |

#### Scenario: Successful insertion with tenant
- GIVEN a valid email with tenant context set by middleware
- WHEN the backend persists the entry
- THEN tenant_id is stored from the current tenant context

#### Scenario: Existing entry migration
- GIVEN waitlist entries existed before multi-tenant
- WHEN the migration runs
- THEN all existing entries have tenant_id set to "AUKALABS"
