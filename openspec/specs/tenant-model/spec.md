# Tenant Model Specification

## Purpose

Tenant model, RLS isolation, and tenant-aware middleware for multi-tenant data boundaries. Every user and resource belongs to exactly one tenant; PostgreSQL Row-Level Security enforces cross-tenant isolation at the database level.

## Requirements

### R1: Tenant Model

The system MUST persist tenants with `id` (UUID PK), `name` (required), `slug` (unique, auto-generated from company name), and `created_at`.

| Field      | Type       | Required | Unique |
|------------|------------|----------|--------|
| id         | UUID       | Yes      | Yes    |
| name       | str        | Yes      | No     |
| slug       | str        | Yes      | Yes    |
| created_at | datetime   | Yes      | No     |

#### Scenario: Tenant created from company name
- GIVEN a registration with company name "Acme Corp"
- WHEN the system generates the tenant
- THEN slug is "acme-corp" and all fields are stored correctly

### R2: tenant_id on User and WaitlistEntry

The system MUST add `tenant_id` (UUID FK to tenants, NOT NULL for User, nullable for WaitlistEntry for migration compatibility) to both models.

| Model         | Field      | Nullable | FK Target |
|---------------|------------|----------|-----------|
| User          | tenant_id  | No       | tenants   |
| WaitlistEntry | tenant_id  | Yes      | tenants   |

#### Scenario: New user has tenant
- GIVEN a registered user
- WHEN the user record is persisted
- THEN tenant_id is set and non-null

### R3: RLS Policies

PostgreSQL MUST enforce RLS on `tenants`, `users`, and `waitlist_entries` tables. Each policy compares the row's `tenant_id` with `current_setting('app.current_tenant_id')::uuid`. Users with `is_superadmin` bypass RLS.

#### Scenario: RLS filters own tenant rows
- GIVEN two tenants A and B with data in `users`
- WHEN tenant A queries `users`
- THEN only tenant A's rows are visible

#### Scenario: Superadmin bypass
- GIVEN a user with `is_superadmin = true`
- WHEN they query across tenants
- THEN all rows are visible

### R4: FastAPI Tenant Middleware

The system MUST provide a FastAPI dependency that decodes the JWT, extracts `tenant_id`, executes `SET LOCAL app.current_tenant_id = '<uuid>'` on the DB session, and sets `request.state.current_tenant_id`.

#### Scenario: Tenant context set from valid JWT
- GIVEN a valid JWT with tenant_id
- WHEN the middleware runs
- THEN SET LOCAL is called and request.state.current_tenant_id is populated

#### Scenario: Missing tenant_id in JWT
- GIVEN a valid JWT without tenant_id
- WHEN the middleware runs
- THEN a 401 error is returned

### R5: Registration Creates Tenant+User Atomically

The registration endpoint MUST accept company name, create a Tenant (with auto-generated slug) and its first User in a single DB transaction, then encode `tenant_id` in the JWT.

#### Scenario: Full registration flow
- GIVEN registration data with email, password, and company name
- WHEN the endpoint processes the request
- THEN a tenant is created, a user is created with that tenant_id, and the JWT includes tenant_id

#### Scenario: Transaction rollback on failure
- GIVEN a registration that creates the tenant but fails on user creation
- WHEN the transaction rolls back
- THEN no orphan tenant exists in the database

### R6: Default "AUKALABS" Tenant Migration

The Alembic migration MUST seed a tenant with name "AUKALABS" and slug "aukalabs".

#### Scenario: Default tenant seeded
- GIVEN a fresh migration up
- WHEN the migration runs
- THEN the "AUKALABS" tenant exists in the tenants table

### R7: Existing Data Migration

The migration MUST assign all existing users to the default "AUKALABS" tenant_id and all existing waitlist entries to that same tenant_id.

#### Scenario: Existing user migrated
- GIVEN a user created before multi-tenant
- WHEN the migration completes
- THEN the user's tenant_id points to "AUKALABS"

#### Scenario: Existing waitlist entry migrated
- GIVEN a waitlist entry created before multi-tenant
- WHEN the migration completes
- THEN the entry's tenant_id points to "AUKALABS"

### R8: Frontend Registration with Company Name

The register form MUST include a company name input. The auth context (AuthProvider) MUST expose `tenant` with `id` and `slug`. The dashboard sidebar MUST display the tenant slug.

#### Scenario: Register form has company field
- GIVEN the register page loads
- WHEN the user fills in the form
- THEN a company name field is present and submitted

#### Scenario: Tenant slug in sidebar
- GIVEN a logged-in user with tenant
- WHEN the dashboard layout renders
- THEN the tenant slug is visible in the sidebar

### R9: Tenant Isolation Enforcement

Cross-tenant queries MUST return empty results for non-admin users. The system MUST NOT expose `tenant_id` in public API responses.

#### Scenario: Cross-tenant query returns empty
- GIVEN user from tenant A queries a resource owned by tenant B
- WHEN the request is processed with RLS active
- THEN the response is empty (200 with [])
