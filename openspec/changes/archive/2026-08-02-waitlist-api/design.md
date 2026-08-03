# Design: Waitlist API

## Technical Approach

Extend the existing backend (FastAPI + async SQLAlchemy) with a `WaitlistEntry` model and `POST /api/v1/waitlist` route. The route validates input, checks a per-email in-memory cooldown, inserts via SQLAlchemy, then fire-and-forgets a Resend confirmation email via httpx. A new `WaitlistSection` component renders between Pricing and Contact on the landing page, posting through the existing `/api/backend/*` Next.js rewrite proxy. This follows every existing pattern: APIRouter prefix + Depends(get_db), Pydantic request models, in-memory SQLite test fixtures, and vitest component tests with fetch stubs.

## Architecture Decisions

### AD1: Resend API Key on Backend (not proxied through Next.js)

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Backend calls Resend directly via httpx | Key on backend .env, one less network hop, simpler error handling | ✅ **Chosen** |
| Backend calls Next.js `/api/send` route | Keeps key in Next.js only, but adds unnecessary internal HTTP hop | ❌ Rejected |

**Rationale**: The existing contact form already routes through Next.js Serverless (Vercel), but the waitlist backend runs on a different process. Proxying email through Next.js adds a second HTTP hop and couples the two services. Adding `RESEND_API_KEY` to the backend `.env` and calling Resend directly from the route handler is simpler, directly testable, and follows the same pattern as the existing `/api/send/route.ts` (just on the backend side).

### AD2: In-Memory Cooldown Dict

| Option | Tradeoff | Decision |
|--------|----------|----------|
| In-memory `dict[str, float]` | Lost on restart, no shared state across workers, zero infrastructure | ✅ **Chosen** |
| DB-backed cooldown | Survives restarts, shared across workers, but adds complexity for Sprint 0 | ❌ Rejected |

**Rationale**: Accepted per proposal scope — in-memory dict is sufficient for staging. A single worker (uvicorn) means no cross-worker races. Will upgrade to DB-backed when production demands it.

### AD3: Fire-and-Forget Email Send

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Fire-and-forget with try/except | Entry persisted even if email fails, simple code | ✅ **Chosen** |
| Transactional (rollback insert on email failure) | Loses the lead when email fails — worse UX | ❌ Rejected |

**Rationale**: The spec explicitly requires entry persistence even when Resend fails (R3: Resend API failure scenario). Fire-and-forget logs warnings and returns 201 regardless of email status.

### AD4: Simple Email Validation

**Choice**: Use `pydantic.EmailStr` server-side (same pattern as `auth.py`), plus basic HTML5 `type="email"` + regex client-side.

**Alternatives considered**: Custom email validation library, third-party verification API.

**Rationale**: `EmailStr` from pydantic[email] is already a dependency (used in `auth.py`). Client-side validation is for UX, not security — the real validation is server-side.

## Data Flow

```
Browser                    Next.js                      Backend                    Resend API
  │                          │                            │                          │
  │  POST /api/backend/      │                            │                          │
  │  /waitlist               │                            │                          │
  │ ──────────────────────►  │                            │                          │
  │                          │  Rewrite to                │                          │
  │                          │  /api/v1/waitlist          │                          │
  │                          │ ────────────────────────►  │                          │
  │                          │                            │  1. Validate input       │
  │                          │                            │  2. Check cooldown       │
  │                          │                            │  3. INSERT waitlist      │
  │                          │                            │                          │
  │                          │                            │  POST /emails            │
  │                          │                            │ ──────────────────────►  │
  │                          │                            │  ◄──── 200 OK ─────────  │
  │                          │                            │                          │
  │                          │  ◄── 201 { entry } ─────── │                          │
  │  ◄──── 201 ──────────────│                            │                          │
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/models/waitlist.py` | Create | `WaitlistEntry` model (id, email unique, company, source, created_at) |
| `backend/app/models/__init__.py` | Modify | Add `WaitlistEntry` to exports |
| `backend/app/database.py` | Modify | Import `WaitlistEntry` model in `init_db()` for `create_all` |
| `backend/app/routes/waitlist.py` | Create | `POST /api/v1/waitlist` with validation, cooldown, insert, Resend email |
| `backend/app/main.py` | Modify | Register `waitlist.router` |
| `backend/app/config.py` | Modify | Add `resend_api_key: str` to `Settings` |
| `backend/.env.example` | Modify | Add `RESEND_API_KEY=` line |
| `backend/tests/test_waitlist.py` | Create | pytest tests for all endpoint scenarios |
| `components/waitlist.tsx` | Create | Waitlist form section with email + company, status states |
| `app/page.tsx` | Modify | Import and render `WaitlistSection` between `PricingSection` and `ContactSection` |
| `lib/api.ts` | Modify | Add `api.waitlist.submit(email, company?)` method |
| `lib/api.test.ts` | Modify | Add tests for `api.waitlist.submit` |

## Interfaces / Contracts

### Backend — Request/Response Models

```python
class WaitlistCreate(BaseModel):
    email: EmailStr
    company: str | None = None

class WaitlistResponse(BaseModel):
    id: str
    email: str
    company: str | None
    created_at: datetime

class ErrorResponse(BaseModel):
    detail: str
```

### Backend — Route

```
POST /api/v1/waitlist
  Body:    { "email": "user@example.com", "company": "Acme" }
  201:     { "id": "uuid", "email": "user@example.com", "company": "Acme", "created_at": "..." }
  409:     { "detail": "Email already registered" }
  422:     { "detail": "Invalid email format" }
  429:     { "detail": "Try again later", "retry-after": 300 }
```

### Frontend — API Domain

```typescript
api.waitlist = {
  submit: (email: string, company?: string) =>
    request<{ id: string; email: string; company: string | null; created_at: string }>(
      "/waitlist",
      { method: "POST", body: JSON.stringify({ email, company }) }
    ),
}
```

### Frontend — Component Props

```typescript
// No external props — self-contained "use client" section component
// Internal state: email, company, status (idle | loading | success | error), errorMessage
```

### Resend Email Template

Simple HTML confirmation with brand styling (matching existing dark theme). Template inlined in route handler:

```html
<div style="font-family:sans-serif; background:#000; color:#fff; padding:20px;">
  <h2 style="color:#00ff99;">Thanks for joining the waitlist!</h2>
  <p>We'll keep you posted on Aukalabs launches and updates.</p>
  <p style="color:#666;">— The Aukalabs Team</p>
</div>
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Backend unit | Model fields + constraints | Use test fixtures, verify SQLAlchemy column types |
| Backend integration | Endpoint scenarios | pytest + httpx AsyncClient + in-memory SQLite (existing conftest pattern). Mock Resend via `httpx_mock` or monkeypatch. |
| Frontend unit | `api.waitlist.submit` | vitest + fetch mock (existing `lib/api.test.ts` pattern) |
| Frontend component | `WaitlistSection` render + submit + error states | vitest + @testing-library/react + userEvent + fetch stub |

### Backend Test Scenarios (R1–R8 coverage)

- 201 on valid email with no company
- 201 on valid email with optional company
- 422 on missing email
- 422 on invalid email format
- 409 on duplicate email (unique constraint)
- 429 on cooldown active (< 5 min)
- 201 on cooldown expired (≥ 5 min)
- Email sent to Resend on successful insert
- 201 + warning logged when Resend fails (fire-and-forget)
- 500 on database failure

### Frontend Test Scenarios

- `waitlist.submit` POSTs to `/waitlist` with email + optional company
- WaitlistSection renders inputs and submit button
- Shows success message after 201
- Shows inline error on invalid email client-side
- Shows error state on API failure

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary. The `/api/backend/*` rewrite is existing infrastructure, not a new routing change.

## Migration / Rollout

No migration required. New table created via `init_db()` → `Base.metadata.create_all` on next backend restart. No data needs transforming.

### Rollback Per Component

1. **Backend route + model**: Remove `waitlist.router` from `main.py`, delete `routes/waitlist.py`, delete `models/waitlist.py`, revert `models/__init__.py`, revert `database.py` import, drop `waitlist_entries` table manually.
2. **Backend config**: Remove `resend_api_key` from `Settings` (or leave — harmless unused field).
3. **Frontend component**: Remove `WaitlistSection` import and rendering from `page.tsx`, delete `components/waitlist.tsx`.
4. **API layer**: Remove `api.waitlist` from `lib/api.ts`.

Each step can be reverted independently without affecting the other.

## Open Questions

- None — all decisions are covered by the spec and verified against existing codebase patterns.
