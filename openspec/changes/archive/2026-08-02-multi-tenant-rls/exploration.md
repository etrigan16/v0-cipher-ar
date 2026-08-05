## Exploration: multi-tenant-rls — Tenant isolation with PostgreSQL Row-Level Security

### Current State

The application has zero multi-tenant awareness today:

- **No Tenant model** exists — every table is tenant-oblivious.
- **User model** (`backend/app/models/user.py`) has `id`, `email`, `name`, `hashed_password`, `is_active`, `mfa_secret`, `mfa_enabled`, `created_at`. No `tenant_id` column.
- **Auth routes** (`backend/app/routes/auth.py`): Registration creates a bare `User` with email/password/name — no tenant context. JWT encodes only `{"sub": user_id}`.
- **get_current_user** dependency looks up `User` by ID from JWT `sub`. No tenant awareness.
- **WaitlistEntry** also has no tenant_id.
- **Frontend** (`app/register/page.tsx`): Registers user, immediately logs in, stores JWT in localStorage, redirects to `/dashboard`. No tenant input in the form.
- **Auth context** (`components/auth-context.tsx`): Stores `user` (id, email, name) and `token` from localStorage. No tenant object.
- **Test infrastructure** (`backend/tests/conftest.py`): SQLite in-memory override — RLS is PostgreSQL-only, so RLS tests CANNOT run under this fixture.
- **JWT payload**: `create_access_token` encodes only `{"sub": user_id, "exp": ...}`. No tenant claim.

### Affected Areas

| File | Why affected |
|------|-------------|
| `backend/app/models/user.py` | Add `tenant_id` FK column to User |
| `backend/app/models/tenant.py` | NEW — Tenant model (id, name, slug, plan, created_at) |
| `backend/app/database.py` | Add RLS helper functions (if inline) |
| `backend/app/routes/auth.py` | Registration: create tenant + user in transaction |
| `backend/app/routes/__init__.py` | (no change, but tenant-awareness propagates) |
| `backend/app/main.py` | Possibly add middleware or startup RLS setup |
| `backend/app/config.py` | May need `enable_rls: bool` for test vs prod |
| `backend/tests/conftest.py` | Can't test RLS in SQLite — document limitation or add real PostgreSQL test fixture |
| `backend/tests/test_auth.py` | Tests need update for tenant context in registration |
| `components/auth-context.tsx` | Add tenant info (id, slug) to auth context |
| `lib/api.ts` | Optionally send tenant header for non-JWT-aware scenarios |
| `app/register/page.tsx` | Add company/slug fields to capture tenant name at registration |
| `app/dashboard/layout.tsx` | Possibly show tenant name in sidebar |

### Approaches

1. **Minimal Tenant Model + PostgreSQL RLS** (recommended)
   - New `Tenant` model: `id (UUID)`, `name`, `slug (unique)`, `plan (enum: free/pro/enterprise)`, `created_at`
   - Add `tenant_id (FK, NOT NULL)` to `User`
   - Add `tenant_id (FK, nullable)` to `WaitlistEntry` (waitlist entries can be pre-tenant)
   - RLS policies on `users`, `waitlist_entries`, and future data tables
   - Middleware: Extract `tenant_id` from JWT, set via `request.state.current_tenant_id` or a context variable
   - Registration flow: create `Tenant` + `User` in a single transaction
   - JWT payload: add `{"tenant_id": ...}` claim
   - Migration: create a "default" tenant for existing users, assign all to it
   - Test strategy: keep SQLite tests for non-RLS logic; add a separate `docker-compose.test.yml` PostgreSQL fixture for RLS-specific tests OR skip RLS tests with a `pytest.mark.skipif` guard
   - Pros: Real tenant isolation at DB level; no risk of missing WHERE filters; clean for future compliance; PostgreSQL-native feature already in the stack
   - Cons: RLS is PostgreSQL-only — test infra limitation; requires learning RLS syntax; migration path messy for existing users
   - Effort: **Medium** (4-5 tasks)

2. **Soft Multi-Tenancy (app-level filtering, no RLS)**
   - Add `tenant_id` to models, JWT, and middleware
   - Every query adds `.where(Model.tenant_id == current_tenant_id)`
   - No PostgreSQL RLS — works with SQLite tests natively
   - Pros: Works with existing SQLite test fixture; simpler mental model; no RLS learning curve
   - Cons: Human error risk (forget a WHERE = data leak to wrong tenant); no DB-level enforcement; scales poorly as tables grow; compliance risk for multi-tenant SaaS
   - Effort: **Low-Medium** (3-4 tasks)

3. **Schema-per-Tenant** (full isolation)
   - Each tenant gets their own PostgreSQL schema
   - Dynamic schema switching via middleware
   - Pros: Maximum isolation; clean separation
   - Cons: Massive complexity; connection pooling nightmare; schema migrations per tenant; WAY over-engineered for MVP stage; testing nightmare
   - Effort: **Very High** (not viable for Sprint 0)

4. **Hybrid: RLS on production + app-level filter for tests**
   - Use RLS in production, app-level `.where()` filtering in all queries
   - Both layers enforce tenant isolation
   - Pros: Best of both worlds — DB enforcement in prod + testable in SQLite
   - Cons: Double maintenance (WHERE + RLS must stay in sync)
   - Effort: **Medium-High**

### Recommendation

**Approach 1: Minimal Tenant Model + PostgreSQL RLS**.

The DoD requirement says "Multi-tenant: dos tenants ven solo sus datos" with RLS policies — this is the explicit ask. RLS is the correct architectural choice for a security SaaS: data leaks between tenants are a catastrophic failure mode, and relying on developers to never forget a `.where()` is naive.

Key design decisions:

1. **Tenant model**: Keep it minimal — `id`, `name`, `slug` (unique, used in URLs/API), `plan`, `created_at`. Slug auto-generated from company name.

2. **Registration flow**: Company name becomes a required field. On registration:
   ```
   BEGIN TX
     INSERT tenant (name=company, slug=generate_slug(company))
     INSERT user (email, name, hashed_password, tenant_id=tenant.id)
   COMMIT
   ```

3. **RLS policies**: Enable RLS on `tenants`, `users`, and all future data tables. Policy: `tenant_id = current_setting('app.current_tenant_id')::uuid`. Use PostgreSQL `SET LOCAL` at connection level.

4. **Middleware**: Create a FastAPI dependency/middleware that decodes JWT, extracts `tenant_id`, sets `SET LOCAL app.current_tenant_id = '...'` on the DB session, and stores `current_tenant_id` in `request.state`.

5. **Existing user migration**: Create a `default-tenant` on first deploy. Assign all existing users to it. Make `tenant_id` NOT NULL only after migration runs.

6. **Frontend**: Add company name field to registration page. Show tenant slug in dashboard sidebar. Add tenant info to AuthProvider context.

7. **Test strategy**: Do NOT try to test RLS in SQLite. Keep SQLite for unit/integration tests of business logic. Add a separate `backend/tests/conftest_postgres.py` or CI-only test with a real PostgreSQL container for RLS policy verification. Mark RLS tests with `pytest.mark.rls` and run them in CI only.

### Risks

- **Migration complexity**: Adding `tenant_id` NOT NULL to existing users requires a default tenant. Need a careful migration plan.
- **RLS learning curve**: Team needs to understand `current_setting`, `SET LOCAL`, policy syntax. Small risk but real.
- **SQLite/RLS incompatibility**: Cannot test RLS in the existing test fixture. Need either: (a) separate PostgreSQL test in CI, or (b) hybrid app-level + RLS approach.
- **Registration UX change**: Adding company name to the registration form adds friction. Consider making it optional? (Risk: then `slug` generation needs fallback logic).
- **Waitlist entries**: Pre-existing waitlist entries have no tenant. Make `tenant_id` nullable on `WaitlistEntry` or leave them tenant-less until they convert.
- **Performance**: `SET LOCAL` per-request adds overhead. Negligible at current scale but worth monitoring.

### Ready for Proposal

**Yes**. The analysis is complete. The orchestrator can proceed to `sdd-propose` with the recommendation for Approach 1. Key ambiguity to resolve: whether company name should be required or optional in the registration form.
