# Tasks: Multi-Tenant RLS

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~420 |
| 400-line budget risk | Medium (override: 800-line budget active) |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | ask-on-risk |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: Medium

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Full backend (models + alembic + middleware + RLS + auth + registration) | PR 1 | `pytest backend/tests/test_auth.py -x -v` | `docker compose up db -d && alembic upgrade head && uvicorn app.main:app` | Revert code + `alembic downgrade -1` |
| 2 | Frontend (form + context + sidebar) | PR 1 | `npm test -- --run` | `npm run dev` on localhost | Revert frontend code |
| 3 | Tests (backend + frontend) | PR 1 | `pytest backend/tests/ -x -v` | `docker compose up db -d && alembic upgrade head && pytest` | Revert test files |

## Phase 1: Foundation

- [x] 1.1 Create `backend/app/models/tenant.py` (Tenant: id UUID PK, name, slug unique, created_at)
- [x] 1.2 Modify `backend/app/models/user.py` — add `tenant_id` FK (UUID, nullable-for-now), `is_superadmin` Bool
- [x] 1.3 Modify `backend/app/models/waitlist.py` — add `tenant_id` FK (UUID, nullable)
- [x] 1.4 Modify `backend/app/models/__init__.py` — import Tenant
- [x] 1.5 Add `alembic` and `python-slugify` to `backend/requirements.txt`
- [x] 1.6 Run `alembic init alembic` inside `backend/`, configure `alembic.ini` for asyncpg
- [x] 1.7 Create Migration 001: create tenants table + add tenant_id cols + seed "AUKALABS" tenant + UPDATE existing users/waitlist SET tenant_id
- [x] 1.8 Create Migration 002: ALTER users ALTER COLUMN tenant_id SET NOT NULL

## Phase 2: Core Implementation

- [x] 2.1 Modify `backend/app/database.py` — register Tenant model in `init_db`
- [x] 2.2 Create `backend/app/middleware/tenant.py` — `get_tenant_context` dep: decode JWT → SET LOCAL → populate `request.state`
- [x] 2.3 Modify `backend/app/utils/tokens.py` — include `tenant_id` in `create_access_token` payload
- [x] 2.4 Modify `backend/app/routes/auth.py` — add `company_name` to `RegisterRequest`; atomic tenant+user creation in transaction
- [x] 2.5 Add startup fallback in `app/main.py` — seed "AUKALABS" tenant if absent (covers fresh deploys)
- [x] 2.6 Add RLS policy SQL in migration 001 or `database.py` startup (tenants, users, waitlist_entries + superadmin bypass)

## Phase 3: Frontend

- [x] 3.1 Modify `lib/api.ts` — `register()` accepts `companyName`; `/me` response type includes `tenant {id, slug}`
- [x] 3.2 Modify `components/auth-context.tsx` — add `Tenant` type; expose `tenant` in context; update register signature
- [x] 3.3 Modify `app/register/page.tsx` — add company name input field, pass to register()
- [x] 3.4 Modify `app/dashboard/layout.tsx` — show `user.tenant.slug` in navbar/sidebar

## Phase 4: Testing

- [x] 4.1 Modify `backend/tests/conftest.py` — document SQLite RLS skip; add tenant context mock fixture
- [x] 4.2 Write test: Tenant model creation + slug generation (pytest, sqlite)
- [x] 4.3 Write test: RegisterRequest Pydantic validation (missing company_name → 422)
- [x] 4.4 Write test: Registration creates tenant+user atomically (assert both rows, FK valid)
- [x] 4.5 Write test: Transaction rollback on user creation failure (no orphan tenant)
- [x] 4.6 Write test: Login returns JWT with `tenant_id` claim
- [x] 4.7 Write test: `/me` endpoint returns `tenant {id, slug}` object
- [x] 4.8 Write test: Middleware rejects JWT without `tenant_id` (401)
- [x] 4.9 Write test: Alembic migration up/down (runs against test PostgreSQL or documented skip)
- [x] 4.10 Write frontend test: register form submits `companyName` (Vitest)
- [x] 4.11 Write frontend test: AuthProvider exposes `tenant` after login (Vitest)
- [x] 4.12 Write frontend test: dashboard sidebar shows tenant slug (Vitest)
