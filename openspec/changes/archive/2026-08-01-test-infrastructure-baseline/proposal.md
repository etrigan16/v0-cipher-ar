# Proposal: Test Infrastructure Baseline

## Intent

Zero tests in either stack, broken lint, no quality gate; strict TDD is impossible without a working `test_command`. This change builds the dependency root: working frontend/backend test harnesses, working lint, quick wins, and minimal secret hardening, so future changes run RED-GREEN-REFACTOR.

## Scope

**In**
- Slice A (frontend): vitest + RTL + jsdom + user-event; `vitest.config.ts`/`vitest.setup.ts`; `test` script; sample tests (utils, api mocked-fetch, auth-context, login page).
- Lint: ESLint 9 flat config (`eslint.config.mjs`) + `eslint-config-next`; working `lint` script.
- Quick wins: fix `package.json` name (assumed `aukalabs`); delete dead `styles/globals.css`.
- Slice B (backend): pytest + pytest-asyncio + httpx + aiosqlite; `backend/tests/` (DB override); health + auth flow tests; portable `sqlalchemy.Uuid` for SQLite (design).
- Hardening: `SECRET_KEY` required from env in `backend/app/config.py`; contact recipient from `CONTACT_EMAIL` in `app/api/send/route.ts`; `.env.example` updates.
- Config: flip `openspec/config.yaml` to strict-TDD-ready; update testing-capabilities cache.

**Out**
- CI (follow-up change); Playwright E2E; ASM/Phishing features; flipping `typescript.ignoreBuildErrors`; docs sync; JWT-in-localStorage and rate-limit debt.

## Capabilities

`openspec/specs/` is empty — no modified capabilities.

### New Capabilities
- `test-infrastructure`: runners, sample tests, scripts for both stacks; strict-TDD config flip.
- `code-quality`: working lint (ESLint 9 flat config, `lint` script).
- `secret-config`: env-required `SECRET_KEY`; env-driven contact email.

### Modified Capabilities
None.

## Approach

Two slices. A: frontend test stack, sample tests, ESLint 9 config, name fix, dead css removal, email parametrization. B: pytest stack, SQLite test DB, auth/health tests, required `SECRET_KEY`. Then config flip + cache update. Verify runs `tsc --noEmit` explicitly until CI lands.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `package.json` | Mod | name, test/lint deps + scripts |
| `vitest.config.ts`, `vitest.setup.ts` | New | frontend harness |
| `eslint.config.mjs` | New | flat config |
| `styles/globals.css` | Removed | dead file |
| `app/api/send/route.ts` | Mod | `CONTACT_EMAIL` env |
| `backend/requirements.txt` | Mod | pytest dev deps |
| `backend/tests/` | New | conftest + auth/health tests |
| `backend/app/config.py` | Mod | `SECRET_KEY` required |
| `backend/app/models/user.py` | Mod | portable `Uuid` |
| `backend/.env.example` | Mod | env var docs |
| `openspec/config.yaml` | Mod | strict-TDD-ready |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Install prerequisites (pnpm, pip) | Med | tasks: install first |
| Next 16 + ESLint 9 compat | Med | minimal config; manual-plugin fallback |
| Postgres UUID vs SQLite | Med | portable `Uuid` (design) |
| 400-line review budget | Med | chained PRs A/B |
| Required SECRET_KEY breaks boot | Low | `.env.example`; conftest env |

## Rollback Plan

Revert per slice: remove new deps/configs/tests, restore `package.json` name, hardcoded recipient, and `SECRET_KEY` default. No migrations; delete new files, `git checkout` modified ones.

## Dependencies

`pnpm install` + backend `pip install` before tests run. Design decision: portable `Uuid` vs Postgres test DB.

## Success Criteria

- [ ] `pnpm test` and `pnpm lint` pass.
- [ ] `pytest` passes (auth + health).
- [ ] Backend boot fails without `SECRET_KEY`; works with it.
- [ ] `openspec/config.yaml` strict-TDD-ready; capabilities cache updated.

## Proposal question round

Assumption to review: `package.json` name → `aukalabs` (product/domain). Alternative: `v0-cipher-ar` (repo name). Confirm before apply.
