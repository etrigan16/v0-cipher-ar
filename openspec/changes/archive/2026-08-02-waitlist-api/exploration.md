## Exploration: waitlist-api

### Current State

**Database**: Async SQLAlchemy with `create_async_engine` + `async_sessionmaker`. `Base = DeclarativeBase`. `init_db()` calls `Base.metadata.create_all` at startup. No Alembic — schema is inline. SQLite test override in conftest uses in-memory SQLite + `StaticPool`.

**Models**: Single model `User` in `backend/app/models/user.py`. Columns: id (UUID), email (unique, indexed), name, hashed_password, is_active, created_at. Models `__init__.py` re-exports `User`. Adding a new model means: (1) new file in models/, (2) import in models/__init__.py, (3) import in database.py `init_db()`.

**Routes**: Three routers — `auth.py` (prefix `/auth`, has actual DB ops), `asm.py` (prefix `/asm`, stub), `phishing.py` (prefix `/phishing`, stub). Pattern: `APIRouter(prefix="/{name}", tags=["{name}"])` + Pydantic request/responses + `async def endpoint(db: AsyncSession = Depends(get_db))`. Routers registered in `main.py` via `app.include_router()`.

**Email (existing)**: `app/api/send/route.ts` — Next.js API route using `resend` npm package. POST handler validates 4 required fields, sends HTML email via `Resend().emails.send()` to `CONTACT_EMAIL` env var. No confirmation email sent to the submitter.

**Frontend API client**: `lib/api.ts` — generic `request<T>()` with auto Bearer token from localStorage. Groups by domain (`api.auth`, `api.asm`, `api.phishing`). All calls target `NEXT_PUBLIC_API_URL` (backend). Contact form does NOT use this client — it does a raw `fetch("/api/send", ...)` directly.

**Landing page**: `app/page.tsx` composes sections in order: Navbar → Hero → TrustedBy → Services → Intelligence → AuditExpress → AttackSurface → Phishing → Pricing → Contact → Footer. **No waitlist section exists.** A `NewsletterSection` component exists in `components/newsletter.tsx` but is NOT rendered on the page and has no backend.

**Rewrites**: `next.config.mjs` proxies `/api/backend/:path*` → `NEXT_PUBLIC_API_URL/:path*`. Backend routes are accessible at `/api/backend/auth/login`, etc.

**Testing**: BE pytests use `AsyncClient(ASGITransport(app=app))` with in-memory SQLite override; FE vitest tests use `vi.fn().mockResolvedValue(...)`. Both green.

**Migration**: No Alembic. Schema evolves via `create_all` — safe for new tables, dangerous for migrations.

### Affected Areas

| File/Dir | Reason |
|----------|--------|
| `backend/app/models/waitlist.py` | New model: WaitlistEntry |
| `backend/app/models/__init__.py` | Export new model |
| `backend/app/routes/waitlist.py` | New router: POST /waitlist |
| `backend/app/main.py` | Register new router |
| `backend/app/database.py` | Import new model in init_db() |
| `backend/tests/test_waitlist.py` | New test file for waitlist endpoint |
| `backend/.env.example` | Add RESEND_API_KEY doc |
| `lib/api.ts` | Add `api.waitlist` domain |
| `lib/api.test.ts` | Add test for waitlist API client call |
| `components/waitlist.tsx` | New waitlist form component |
| `app/page.tsx` | Import + render WaitlistSection |
| `app/api/send-waitlist/route.ts` | Optional: if email confirmation via Next.js route |

### Approaches

1. **FastAPI backend endpoint** — New router `backend/app/routes/waitlist.py` with `POST /waitlist`, new model `WaitlistEntry` in backend.
   - Pros: Consistent with existing auth/asm/phishing pattern; async SQLAlchemy already available; DB test pattern exists; single endpoint stores + can trigger email via Resend REST API (`httpx`); access to auth middleware if needed later.
   - Cons: Email sending from Python requires httpx call to Resend API (no Python SDK used currently); RESEND_API_KEY needs to be available in backend env.
   - Effort: Medium (~305 lines total)

2. **Next.js API route + DB call** — Dual route: `app/api/waitlist/route.ts` stores data via backend API call or Prisma, plus sends confirmation via Resend.
   - Pros: Reuses Resend SDK directly (already in package.json); simpler email templating.
   - Cons: No direct DB access from Next.js (no ORM there); would need to either (a) add Prisma/Drizzle to frontend, (b) call backend API from the route, or (c) store only in backend. Extra network hop or dual schema management.
   - Effort: Medium-High (extra complexity layer)

3. **Hybrid: Backend stores + Next.js sends email** — Backend endpoint stores the entry; frontend component calls both backend POST and `/api/send-waitlist` (Next.js route for confirmation email).
   - Pros: Each service does what it's best at (backend → DB, Next.js → email via Resend SDK); no new email integration in Python.
   - Cons: Two round-trips from the client; error handling is complex (DB succeeded but email failed); network-dependent user experience.
   - Effort: Medium (more moving parts)

### Recommendation

**Approach 1 (FastAPI backend endpoint)** is the strongest choice.

Reasoning:
1. The Sprint 0 DoD explicitly requires "guarda en BD + email enviado" — the DB is the backend's territory.
2. The backend already has an established router pattern, async SQLAlchemy, and a proven test fixture.
3. Sending email from Python is straightforward: `httpx` is already in the dependency tree, and Resend's REST API is just a POST with an API key header. No Python SDK needed.
4. The form sends a single POST → the backend stores + emails in one transaction. Simpler client logic.
5. The existing rewrite proxy (`/api/backend/waitlist`) makes this accessible from the frontend with zero CORS setup.
6. Lines stay under the 400-line PR budget.

Only additional concern: RESEND_API_KEY must be added to the backend environment (currently only in Next.js `.env.local`). This is a one-line config change.

**Frontend placement**: Insert `WaitlistSection` between `PricingSection` and `ContactSection` on the landing page. This is the natural flow: user sees pricing, then joins waitlist, then contacts.

**Schema**:

| Column | Type | Required | Notes |
|--------|------|----------|-------|
| id | UUID | PK | auto |
| email | String | Yes | unique, indexed |
| company | String | No | nullable |
| company_size | String | No | enum: "1-10","11-50","51-200","201-500","500+" |
| role | String | No | nullable |
| source | String | No | default "landing" |
| created_at | DateTime | auto | server_default now() |

### Risks

- **RESEND_API_KEY not in backend env**: Currently only in Next.js `.env.local`. Must be added to backend environment or `.env` file. Backend will fail to send confirmation if missing.
- **No rate limiting**: Public form endpoint is vulnerable to spam. Mitigation: add a simple cooldown check (reject if same email submitted within last hour) at the endpoint level.
- **No Alembic**: Schema evolution via `create_all` works for new tables but there's no migration audit trail. Acceptable for Sprint 0 but should be addressed in a future sprint.
- **Email deliverability**: Confirmation email to user's inbox may land in spam. Use Resend's verified domain (`aukalabs.com`), same as the contact form from address.
- **Duplicate submissions**: Without unique constraint on email, users could submit multiple times. Add a unique constraint on email with ON CONFLICT handling or a pre-check.

### Ready for Proposal

Yes. The architecture is clear, the approach is consistent with existing patterns, and the effort is well within the review budget. Proceed to `sdd-propose`.
