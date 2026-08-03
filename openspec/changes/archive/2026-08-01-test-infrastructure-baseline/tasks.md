# Tasks: Test Infrastructure Baseline

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~430 (A ≈ 270, B ≈ 160, flip ≈ 5) |
| 400-line budget risk | Medium |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 (Slice A) → PR 2 (Slice B + flip) |
| Delivery strategy | ask-on-risk |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: Medium

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| A | Frontend harness + lint + quick wins (Phase 2) | PR 1 | `pnpm test && pnpm lint` | `tsc --noEmit` type gate | Revert package.json; delete vitest/eslint configs + tests |
| B | Backend pytest + secret hardening (Phase 3) | PR 2 | `cd backend && pytest` | SQLite ASGITransport; boot fails w/o SECRET_KEY | Revert config/user/requirements/.env.example; delete backend/tests/ |

## Phase 1: Install Prerequisites (hard gate)

- [x] 0.1 `pnpm install` at repo root — lockfile resolves
- [x] 0.2 `pip install -r backend/requirements.txt` in a Python env
- [x] 0.3 Gate: 0.1 + 0.2 pass before any later task

## Phase 2: Slice A — Frontend Harness + Lint (PR 1)

- [x] 2.1 `package.json`: name `aukalabs`; devDeps vitest, @vitejs/plugin-react, @testing-library/react, @testing-library/jest-dom, @testing-library/user-event, jsdom, eslint@^9, eslint-config-next@^16.2.4; script `"test": "vitest run"`
- [x] 2.2 Create `vitest.config.ts` (react, jsdom, setup, `@` alias) + `vitest.setup.ts` (jest-dom, cleanup)
- [x] 2.3 Create `eslint.config.mjs` (D2 flat; FlatCompat fallback); AC: `pnpm lint` exits 0
- [x] 2.4 Create `lib/utils.test.ts` — `cn()` behavior
- [x] 2.5 Create `lib/api.test.ts` — mocked fetch: auth calls, Bearer header, errors
- [x] 2.6 Create `components/auth-context.test.tsx` — login/logout/mount-restore
- [x] 2.7 Create `app/login/page.test.tsx` — mock next/navigation; success/error paths
- [x] 2.8 Delete `styles/globals.css`; no references remain
- [x] 2.9 `app/api/send/route.ts`: `to` = `CONTACT_EMAIL`; unset → 500, no send
- [x] 2.10 Gate: `pnpm test && pnpm lint && pnpm exec tsc --noEmit`

## Phase 3: Slice B — Backend Harness + Hardening (PR 2)

- [x] 3.1 `backend/requirements.txt` + pytest, pytest-asyncio, httpx, aiosqlite; `backend/pytest.ini` (asyncio auto, pythonpath, testpaths)
- [x] 3.2 Create `backend/tests/conftest.py` (D4: SECRET_KEY first, StaticPool SQLite, create_all, get_db override, ASGITransport)
- [x] 3.3 RED: `test_health.py` + `test_auth.py` (register 201/dup 400, login 200/401, /auth/me) — fail until 3.4
- [x] 3.4 GREEN: `backend/app/models/user.py` → `sqlalchemy.Uuid`
- [x] 3.5 RED: `test_config.py` — unset SECRET_KEY raises ValidationError
- [x] 3.6 GREEN: `backend/app/config.py` — `secret_key` required, no default
- [x] 3.7 `backend/.env.example`: SECRET_KEY + CONTACT_EMAIL required markers
- [x] 3.8 Gate: `cd backend && pytest`; boot without SECRET_KEY fails

## Phase 4: Config Flip + Capabilities Cache

- [x] 4.1 `openspec/config.yaml` (D6): tdd true, test_command, verify values
- [x] 4.2 Engram `sdd/v0-cipher-ar/testing-capabilities` → strict TDD, vitest + pytest, lint ok
- [x] 4.3 Final gate: `pnpm test && pnpm lint && cd backend && pytest`; `tsc --noEmit` clean
