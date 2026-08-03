# Design: Test Infrastructure Baseline

## Technical Approach

Build the dependency root for strict TDD in two reviewable slices. Slice A wires a vitest + RTL harness and restores ESLint 9 (flat config) on the frontend; Slice B wires pytest + httpx on an aiosqlite SQLite test DB and hardens secrets. Both slices end green, then `openspec/config.yaml` flips to strict TDD and the testing-capabilities cache updates. Tests use in-memory SQLite and mocked fetch — no external Postgres or network. Slices map to chained PRs (A → B) under the 400-line budget.

## Architecture Decisions

### D1: Postgres-UUID portability — portable `sqlalchemy.Uuid`

| Option | Tradeoff | Decision |
|---|---|---|
| `sqlalchemy.Uuid` on `user.id` | One-line model change; native UUID on Postgres, CHAR(32) on SQLite; no Docker | **Chosen** |
| Postgres test DB (Docker/testcontainers) | Real dialect, but needs Docker at test time; heavy for a baseline | Rejected |
| Keep `postgresql.UUID`, skip DB tests | Loses the auth-flow DB requirement | Rejected |

**Rationale**: `Uuid` stores `uuid.UUID` and coerces string binds (JWT `sub`) on both dialects, so `get_current_user`'s `User.id == user_id` needs no change. `create_all` is the only DDL path (no Alembic), so no migration tooling is touched. **Impact**: `backend/app/models/user.py` — `Column(UUID(as_uuid=True), …)` → `Column(Uuid, …)` (import `Uuid` from `sqlalchemy`); `backend/tests/conftest.py` uses `sqlite+aiosqlite:///:memory:`; a RED `/auth/me` test proves str→UUID coercion.

### D2: Next 16 + ESLint 9 flat config

| Option | Tradeoff | Decision |
|---|---|---|
| Native flat config: `eslint-config-next/core-web-vitals` + `/typescript` | Official Next 16 pattern; peer `eslint >=9` | **Chosen** |
| FlatCompat bridging `.eslintrc` presets | Works if pinned config lags | Fallback |
| Manual `@typescript-eslint` ruleset | Duplicates what Next ships | Rejected |

Minimal `eslint.config.mjs`:

```js
import { defineConfig, globalIgnores } from "eslint/config"
import nextVitals from "eslint-config-next/core-web-vitals"
import nextTs from "eslint-config-next/typescript"

export default defineConfig([
  ...nextVitals, ...nextTs,
  globalIgnores([".next/**", "out/**", "build/**", "next-env.d.ts"]),
])
```

Deps: `eslint@^9`, `eslint-config-next@^16.2.4` (match `next`). **Fallback**: if the pinned `eslint-config-next` lacks flat-config exports, wrap `next/core-web-vitals` + `next/typescript` via `FlatCompat` from `@eslint/eslintrc`. `lint` script stays `eslint .` (ESLint 9 ignores non-JS dirs like `backend/`).

### D3: Frontend harness — vitest

- `vitest.config.ts`: `plugins: [react()]`, `test.environment: "jsdom"`, `setupFiles: ["./vitest.setup.ts"]`, `include: ["**/*.test.{ts,tsx}"]`, `resolve.alias: { "@": <repo root> }` (mirrors tsconfig `@/*`).
- `vitest.setup.ts`: `import "@testing-library/jest-dom/vitest"` + RTL `afterEach(cleanup)` (no `globals: true`; tests import `describe/it/expect/vi` explicitly, so tsconfig is untouched).
- Script: `"test": "vitest run"`. Dev deps: `vitest`, `@vitejs/plugin-react`, `@testing-library/react`, `@testing-library/jest-dom`, `@testing-library/user-event`, `jsdom`.
- Login-page test mocks `next/navigation` (`useRouter` → `push: vi.fn()`); fetch mocked globally per file.

### D4: Backend harness — pytest + aiosqlite `get_db` override

`backend/tests/conftest.py` (no production change to `database.py`):

```python
import os
os.environ["SECRET_KEY"] = "test-secret"   # BEFORE app imports (config reads env at import)
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db
from app.main import app

engine = create_async_engine("sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False}, poolclass=StaticPool)
Session = async_sessionmaker(engine, expire_on_commit=False)

async def override_get_db():
    async with Session() as s:
        yield s

@pytest_asyncio.fixture
async def client():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
```

- `ASGITransport` never runs lifespan → startup `init_db()` (real Postgres) never fires in tests.
- `backend/pytest.ini`: `asyncio_mode = auto`, `pythonpath = .`, `testpaths = tests`.
- `backend/requirements.txt` + `pytest`, `pytest-asyncio`, `httpx`, `aiosqlite`.

### D5: Test isolation

- Frontend: vitest file-isolated jsdom; RTL cleanup per test; fetch mocked per file.
- Backend: one StaticPool in-memory engine (single connection keeps the DB alive), `create_all` once, overrides cleared in teardown; unique emails per test avoid duplicate-key cross-talk.
- Secret unit test: `Settings(_env_file=None)` with `SECRET_KEY` deleted raises `ValidationError` (module-level `settings` already bound with env set at import).

### D6: Config flip — exact values

```yaml
apply:
  tdd: true
  test_command: "pnpm test && cd backend && pytest"
verify:
  test_command: "pnpm test && cd backend && pytest"
  build_command: "pnpm build"
  coverage_threshold: 0
```

Coverage stays `0`: no coverage tool is installed in this change (harness-only). `pnpm lint` and `tsc --noEmit` run as explicit quality-gate tasks until CI lands. Testing-capabilities cache updated: strict TDD enabled, vitest + pytest.

## Sequence Diagrams

**Backend auth test flow**

```
pytest → conftest: set SECRET_KEY env (before app imports)
conftest → engine(sqlite+aiosqlite, StaticPool): create_all
conftest → app.dependency_overrides[get_db] = override_get_db
test → AsyncClient(ASGITransport(app))         # no lifespan → no Postgres
  POST /auth/register → 201
  POST /auth/login    → 200 + token
  GET  /auth/me (Bearer) → 200                 # proves Uuid str coercion
teardown → dependency_overrides.clear()
```

**DB override wiring**

```
fixture client
 ├─ create_async_engine(sqlite+aiosqlite:///:memory:, StaticPool, check_same_thread=False)
 ├─ conn.run_sync(Base.metadata.create_all)
 ├─ override_get_db(): yield Session()         # replaces real async_session
 ├─ app.dependency_overrides[get_db] = override_get_db
 ├─ yield AsyncClient(ASGITransport(app=app), base_url="http://test")
 └─ teardown: overrides.clear(); engine.dispose()
```

**ESLint wiring**

```
pnpm lint → eslint . (ESLint 9 discovers eslint.config.mjs at root)
eslint.config.mjs → defineConfig([...nextVitals, ...nextTs, globalIgnores(...)])
→ exit 0 on clean tree; violations reported by name
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `package.json` | Modify | name → `aukalabs`; devDeps (vitest, RTL, eslint, eslint-config-next); `"test": "vitest run"` |
| `vitest.config.ts`, `vitest.setup.ts` | Create | jsdom harness, `@/*` alias, RTL cleanup |
| `eslint.config.mjs` | Create | flat config per D2 |
| `lib/utils.test.ts`, `lib/api.test.ts`, `components/auth-context.test.tsx`, `app/login/page.test.tsx` | Create | sample frontend tests |
| `styles/globals.css` | Delete | dead — no imports; `components.json` → `app/globals.css` |
| `app/api/send/route.ts` | Modify | recipient from `CONTACT_EMAIL`; unset → 500, no fallback |
| `backend/requirements.txt` | Modify | + pytest, pytest-asyncio, httpx, aiosqlite |
| `backend/pytest.ini` | Create | asyncio auto, pythonpath, testpaths |
| `backend/tests/conftest.py`, `test_health.py`, `test_auth.py`, `test_config.py` | Create | DB override + health/auth flow + secret unit |
| `backend/app/config.py` | Modify | `secret_key: str` required, no default |
| `backend/app/models/user.py` | Modify | `Uuid` per D1 |
| `backend/.env.example` | Modify | document `SECRET_KEY`, `CONTACT_EMAIL` as required |
| `openspec/config.yaml` | Modify | strict-TDD values per D6 |

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit (FE) | `cn()`, api auth calls (mocked fetch), AuthProvider login/logout/me | vitest + RTL + jsdom |
| Unit (BE) | Settings fails without `SECRET_KEY` | pytest, `_env_file=None` |
| Integration (BE) | `/health`; register (201, duplicate 400), login (200, bad creds 401), `/auth/me` (valid/invalid token) | pytest + httpx ASGITransport + aiosqlite |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary is introduced (scripts/config values are declarative; `next.config.mjs` unchanged).

## Migration / Rollout

No data migration. Rollback per slice: delete new files/deps and `git checkout` modified ones. `SECRET_KEY` becomes required — `.env` must set it before boot (documented in `backend/.env.example`).

## Open Questions

- None blocking. Tasks note: confirm `eslint-config-next@16.x` flat exports at install time; else FlatCompat fallback (D2).
