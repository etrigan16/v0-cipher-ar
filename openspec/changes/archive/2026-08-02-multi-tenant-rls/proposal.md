# Proposal: Multi-Tenant RLS

## Intent

Add tenant isolation via PostgreSQL Row-Level Security. Without it, the platform has no data boundaries between tenants — a catastrophic failure for a security SaaS. Registration must atomically create a tenant and its first user.

## Scope

### In Scope
- New `Tenant` model (id, name, slug, created_at) + `tenant_id` FK on `User` and `WaitlistEntry`
- SQLAlchemy migration: create tenants table, add tenant_id columns, assign existing users+waitlist to default "AUKALABS" tenant
- PostgreSQL RLS policies on `tenants`, `users`, `waitlist_entries` using `SET LOCAL app.current_tenant_id`
- FastAPI middleware dependency: decode JWT → extract tenant_id → set session context + `request.state.current_tenant_id`
- Registration flow: accept company name → create Tenant + User in a single transaction → encode `tenant_id` in JWT
- Frontend: add company name field to register form, surface tenant slug in dashboard sidebar, add `tenant` to `AuthProvider` context

### Out of Scope
- Multi-user tenant (invite flow, team management) — deferred
- Plan/billing field on Tenant — deferred
- Automated RLS tests in CI (PostgreSQL-only feature) — skip; test via middleware verification + manual staging
- Schema-per-tenant isolation — over-engineered for MVP

## Capabilities

### New Capabilities
- `tenant-model`: Tenant model schema, slug auto-generation, RLS policy configuration, tenant context middleware, tenant-aware JWT encoding, registration flow with atomic tenant+user creation

### Modified Capabilities
- `waitlist`: WaitlistEntry gains `tenant_id` (FK) column; existing entries migrated to default tenant

## Approach

Add a `Tenant` model (id UUID, name, slug unique, created_at) to the data layer. Add `tenant_id` FK to `User` and `WaitlistEntry`. Create a migration that seeds a "AUKALABS" default tenant and assigns all existing users and waitlist entries to it. Enable RLS on `tenants`, `users`, and `waitlist_entries` with policy `tenant_id = current_setting('app.current_tenant_id')::uuid`. Create a FastAPI dependency that decodes the JWT, extracts `tenant_id`, calls `SET LOCAL` on the DB session, and populates `request.state`. On registration, accept company name, generate slug, and create Tenant + User in a single transaction with `tenant_id` in the JWT payload. On the frontend, add a company name field to the register form and surface the tenant slug in the dashboard sidebar.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/models/tenant.py` | New | Tenant SQLAlchemy model |
| `backend/app/models/user.py` | Modified | Add tenant_id FK column |
| `backend/app/models/waitlist.py` | Modified | Add tenant_id FK column (nullable) |
| `backend/app/routes/auth.py` | Modified | Registration creates tenant+user atomically |
| `backend/app/middleware/tenant.py` | New | JWT → SET LOCAL + request.state middleware |
| `backend/app/database.py` | Modified | RLS setup at engine init |
| `backend/alembic/*` | New | Migration: tenants table + tenant_id + default seed |
| `backend/tests/conftest.py` | Modified | Skip RLS in SQLite; document limitation |
| `backend/tests/test_auth.py` | Modified | Update for tenant context in registration |
| `components/auth-context.tsx` | Modified | Add tenant id + slug to auth context |
| `lib/api.ts` | Modified | Optionally send tenant header |
| `app/register/page.tsx` | Modified | Add company name field |
| `app/dashboard/layout.tsx` | Modified | Show tenant name/slug in sidebar |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Migration of existing users to default tenant fails | Low | Run as transactional migration; test in staging first |
| RLS misconfiguration leaks data between tenants | Low | Test each policy explicitly in staging; defense-in-depth with middleware check |
| SET LOCAL per-request overhead | Low | Negligible at current scale; monitor if needed |
| Registration UX friction (added field) | Low | Company name is a single field; slug auto-generated |

## Rollback Plan

1. Roll back the Alembic migration: downgrade removes tenant_id columns and tenants table
2. Revert middleware/auth changes to code
3. Existing users return to single-tenant state (all data preserved via default tenant)
4. DB-level revert is safe because tenant_id FK is NOT NULL only after migration completes

## Dependencies

- PostgreSQL 14+ required (RLS is PG-specific); existing `asyncpg` driver already supports it

## Success Criteria

- [ ] Registration flow creates Tenant + User atomically with correct tenant_id in JWT
- [ ] RLS policies prevent cross-tenant data access (verified via manual staging query)
- [ ] Migration assigns all existing users and waitlist entries to "AUKALABS" default tenant
- [ ] Frontend shows tenant context in sidebar and captures company name on registration
- [ ] All existing unit/integration tests pass (SQLite fixture skips RLS tests)
