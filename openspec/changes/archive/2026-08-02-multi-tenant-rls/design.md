# Design: Multi-Tenant RLS

## Technical Approach

Add a `Tenant` model with UUID PK, `name`, and unique `slug`. Add `tenant_id` FK to `User` (NOT NULL) and `WaitlistEntry` (nullable). Enable PostgreSQL Row-Level Security on all three tables with policy `tenant_id = current_setting('app.current_tenant_id')::uuid`. Wire a FastAPI dependency that extracts `tenant_id` from the JWT and calls `SET LOCAL app.current_tenant_id` on each request's DB session. Registration creates Tenant + User in one transaction. Startup seeds the default "AUKALABS" tenant for existing data. Add `alembic` for schema versioning. Frontend adds `company_name` to registration, exposes `tenant` in auth context, and shows tenant slug in sidebar.

References: tenant-model spec (R1–R9), waitlist spec (R1 modified).

## Architecture Decisions

### Decision: RLS via `SET LOCAL` instead of schema-per-tenant

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Row-Level Security with `SET LOCAL` | Single schema, one policy per table, ~5 LOC per table | ✅ Chosen — matches MVP scope, minimal complexity |
| Schema-per-tenant (PostgreSQL schemas) | Full isolation, but complex migrations, connection management, massive overhead for MVP | ❌ Rejected — deferred to post-MVP |
| Application-level filtering (WHERE tenant_id = X) | Works on any DB, but easy to miss a query → data leak | ❌ Rejected — RLS is defense-in-depth at the DB layer |

### Decision: Alembic for migration (new to project)

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Alembic | Standard tool, proper up/down, team-shareable | ✅ Chosen — project needs versioned migrations going forward |
| `init_db()` `create_all` only | Current pattern — no downgrade, no history | ❌ Rejected — schema changes require proper migrations |

### Decision: Slug auto-generation from company name

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Slugify from `python-slugify` | Handles Unicode, edge cases, well-tested | ✅ Chosen — add to `requirements.txt` |
| Manual regex slug | Fewer deps, but fragile for non-ASCII | ❌ Rejected — company names can contain accented chars |

### Decision: Superadmin bypass via subquery instead of separate policy

Single `USING` clause: `tenant_id = current_setting(...) OR is_superadmin`. Simpler than a separate `WITH CHECK` policy. Superadmin flag lives on the `users` table; the policy subquery reads `current_setting('app.current_user_id')` to check `is_superadmin`.

## Data Flow

```
Registration:
  Client POST /auth/register {email, password, name, company_name}
    → Tenant created (slug from company_name)
    → User created (hashed_password, tenant_id FK)
    → JWT {sub: user.id, tenant_id: tenant.id}
    → Response {id, email, name}

Every authenticated request:
  Client sends Authorization: Bearer <JWT>
    → Middleware (get_tenant_context) decodes JWT
    → Extracts tenant_id
    → SET LOCAL app.current_tenant_id = '<uuid>'
    → SET LOCAL app.current_user_id = '<uuid>'
    → request.state.current_tenant_id populated
    → Downstream queries filtered by RLS policy
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/models/__init__.py` | Modify | Add `Tenant` import |
| `backend/app/models/tenant.py` | **Create** | Tenant model: id (UUID PK), name, slug (unique), created_at |
| `backend/app/models/user.py` | Modify | Add `tenant_id` FK column (ForeignKey), `is_superadmin` Boolean |
| `backend/app/models/waitlist.py` | Modify | Add `tenant_id` FK column (nullable) |
| `backend/app/middleware/tenant.py` | **Create** | `get_tenant_context` dependency: decode JWT → SET LOCAL → request.state |
| `backend/app/database.py` | Modify | Register Tenant model in `init_db`; add RLS enable on startup |
| `backend/app/routes/auth.py` | Modify | `RegisterRequest` gains `company_name`; registration creates Tenant+User in transaction; `create_access_token` includes `tenant_id` |
| `backend/app/utils/tokens.py` | Modify | `create_partial_token` carries `tenant_id` from auth route |
| `backend/alembic/` | **Create** | Alembic init + migration for tenants table, tenant_id columns, default seed |
| `backend/alembic.ini` | **Create** | Alembic config |
| `backend/requirements.txt` | Modify | Add `alembic`, `python-slugify` |
| `backend/tests/conftest.py` | Modify | Document SQLite RLS skip; fixture for tenant context mock |
| `backend/tests/test_auth.py` | Modify | Update register payloads to include `company_name` |
| `components/auth-context.tsx` | Modify | Add `tenant: {id, slug}` to `AuthContextType`; update `register` signature; parse tenant from /me response |
| `lib/api.ts` | Modify | `register` takes `companyName`; `/me` response type includes `tenant` |
| `app/register/page.tsx` | Modify | Add `companyName` input field |
| `app/dashboard/layout.tsx` | Modify | Show `user.tenant.slug` in navbar |

## Interfaces / Contracts

```python
# backend/app/models/tenant.py
class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(CoercingUuid(), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Modified User — adds tenant_id FK
class User(Base):
    __tablename__ = "users"
    # ... existing columns ...
    tenant_id = Column(CoercingUuid(), ForeignKey("tenants.id"), nullable=False)
    is_superadmin = Column(Boolean, default=False, nullable=False)

# WaitlistEntry — adds nullable tenant_id FK  
class WaitlistEntry(Base):
    __tablename__ = "waitlist_entries"
    # ... existing columns ...
    tenant_id = Column(CoercingUuid(), ForeignKey("tenants.id"), nullable=True)

# Registration request (modified)
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    company_name: str   # NEW
```

```python
# JWT claims (modified create_access_token)
{
    "sub": str(user.id),
    "tenant_id": str(tenant.id),  # NEW
    "exp": ...
}

# Middleware dependency
async def get_tenant_context(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> None:
    payload = jwt.decode(credentials.credentials, ...)
    tenant_id = payload.get("tenant_id")
    if not tenant_id:
        raise HTTPException(401)
    await db.execute(text(f"SET LOCAL app.current_tenant_id = '{tenant_id}'"))
    await db.execute(text(f"SET LOCAL app.current_user_id = '{payload['sub']}'"))
    request.state.current_tenant_id = tenant_id

# RLS policies (applied in init_db + migration)
CREATE POLICY tenant_isolation ON users
    FOR ALL USING (
        tenant_id = current_setting('app.current_tenant_id')::uuid
        OR EXISTS (
            SELECT 1 FROM users WHERE id = current_setting('app.current_user_id')::uuid AND is_superadmin = true
        )
    );
-- Same pattern for tenants (USING id = ...) and waitlist_entries (USING tenant_id = ...)
```

```typescript
// Modified AuthContextType
type Tenant = { id: string; slug: string }
type User = { id: string; email: string; name: string; tenant: Tenant }

// Modified register signature
type AuthContextType = {
  // ...existing...
  register: (email: string, password: string, name: string, companyName: string) => Promise<void>
  // ...existing...
}

// API register
register: (email: string, password: string, name: string, companyName: string) =>
  request<{ id: string; email: string; name: string; tenant: { id: string; slug: string } }>(
    "/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, name, company_name: companyName }),
  }),
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `Tenant` model creation, slug generation | Pytest with SQLite — `python-slugify` output, constraint enforcement |
| Unit | `RegisterRequest` Pydantic validation | Pytest — missing `company_name` → 422 |
| Unit | `create_access_token` includes `tenant_id` | Unit test on `tokens.py` |
| Integration | Registration creates tenant+user atomically | Pytest — assert both rows exist, FK valid |
| Integration | Transaction rollback on user creation failure | Pytest — mock user insert to fail, assert no orphan tenant |
| Integration | Login returns JWT with `tenant_id` | Pytest — decode JWT, verify claim |
| Integration | `/me` returns `tenant` object | Pytest — assert `tenant.id` and `tenant.slug` in response |
| Integration | Waitlist entry stores `tenant_id` from context | Pytest — mock tenant context, assert FK |
| Manual | RLS prevents cross-tenant queries | Staging query: user A cannot see user B's rows |
| Manual | Superadmin bypasses RLS | Staging query: is_superadmin=true sees all rows |
| Integration | Alembic migration up/down | Pytest with test PostgreSQL (or documented CI test) |
| Frontend | Registration form submits `companyName` | Vitest — form submission payload |
| Frontend | AuthProvider exposes `tenant` | Vitest — context after login |
| Frontend | Dashboard sidebar shows tenant slug | Vitest — layout renders slug |

**RLS caveat**: SQLite does not support `SET LOCAL` or `current_setting`. RLS-specific tests MUST run against PostgreSQL (staging or CI service). The existing test suite continues with SQLite for model/logic tests; RLS test fixtures will skip in SQLite via `pytest.skip()`.

## Threat Matrix

**N/A** — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary. The change is entirely data-layer isolation and API middleware.

## Migration / Rollout

**Alembic migration plan** (new to project — must `alembic init alembic` first):

1. **Migration 001**: Create `tenants` table. Add `tenant_id` (nullable UUID, FK) to `users` and `waitlist_entries`. Add `is_superadmin` (Boolean, default false) to `users`.
2. **Data migration** (same migration, after DDL): INSERT "AUKALABS" tenant. UPDATE users SET tenant_id = (SELECT id FROM tenants WHERE slug = 'aukalabs'). UPDATE waitlist_entries SET tenant_id = (SELECT id FROM tenants WHERE slug = 'aukalabs').
3. **Migration 002**: ALTER users ALTER COLUMN tenant_id SET NOT NULL.
4. **Startup fallback** (`app/main.py` startup event): If "AUKALABS" tenant does not exist, create it. Assign any users/waitlist entries with NULL tenant_id. This covers fresh deployments where Alembic hasn't run.

**Rollout order**: Deploy backend first (migration + middleware code). Then deploy frontend. Old frontend calls without `company_name` will get 422 — coordinate deployment window.

**Rollback**: Alembic downgrade drops tenant_id columns + tenants table. Revert code. Non-nullable constraint on User makes downgrade safe only if no new data was added post-migration.

## Open Questions

- None — all decisions are scoped per the proposal and specs.
