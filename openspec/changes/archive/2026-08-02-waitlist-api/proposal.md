# Proposal: Waitlist API

## Intent

Capture early adopter leads from the landing page. Currently no lightweight lead capture exists — only a Contact form for inquiries. The waitlist fills this gap with email + optional company.

## Scope

### In Scope
- `WaitlistEntry` model (email required + unique, company optional)
- `POST /waitlist` endpoint with async SQLAlchemy storage + Resend confirmation email
- 5-min rate limit per email (in-memory cooldown dict)
- Frontend `WaitlistSection` component between Pricing and Contact
- BE tests (pytest) + FE tests (vitest) following existing patterns

### Out of Scope
- Company size / role fields, admin notification email, Airtable/Sheets sync, Alembic, OAuth/SSO

## Capabilities

### New Capabilities
- `waitlist`: Lead capture for early adopter registration. Email required + unique, company optional. Auto confirmation via Resend. Rate-limited per email (5-min cooldown).

### Modified Capabilities
None

## Approach

Backend handles the full flow: async SQLAlchemy insert, then Resend confirmation via httpx POST to Resend REST API. Frontend POSTs to `/api/backend/waitlist` through existing Next.js rewrite proxy. Rate limit via in-memory dict checking last submission timestamp per email. New section rendered between Pricing and Contact on landing page.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/models/waitlist.py` | New | WaitlistEntry model |
| `backend/app/models/__init__.py` | Mod | Export WaitlistEntry |
| `backend/app/database.py` | Mod | Import model for create_all |
| `backend/app/routes/waitlist.py` | New | POST /waitlist endpoint |
| `backend/app/main.py` | Mod | Register new router |
| `backend/tests/test_waitlist.py` | New | BE tests |
| `backend/.env.example` | Mod | Document RESEND_API_KEY |
| `components/waitlist.tsx` | New | Waitlist form section |
| `app/page.tsx` | Mod | Render WaitlistSection between Pricing and Contact |
| `lib/api.ts` + `lib/api.test.ts` | Mod | Add `api.waitlist` domain + test |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| RESEND_API_KEY missing in backend env | Med | Document in .env.example; CI test with dummy key |
| Cooldown dict lost on server restart | Low | Accept for Sprint 0; upgrade to DB-backed later |
| Confirmation email in spam | Med | Resend verified domain, same sender as contact form |
| Duplicate submission race | Low | Unique constraint + try/except rollback |

## Rollback Plan

Remove WaitlistSection from `page.tsx`. Comment out router in `main.py`. Drop `WaitlistEntry` table. Delete model file and export.

## Dependencies

- RESEND_API_KEY added to backend environment (currently only in Next.js `.env.local`)

## Success Criteria

- [ ] POST valid email → 201 + confirmation email sent via Resend
- [ ] Duplicate email → 409 Conflict
- [ ] Same email within 5 min → 429 Too Many Requests
- [ ] WaitlistSection renders between Pricing and Contact
- [ ] All BE + FE tests pass (existing + new)
- [ ] Confirmation email arrives (Resend verified domain)
