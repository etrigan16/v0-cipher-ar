# Waitlist Specification

## Purpose

Lead capture for early adopter registration on the landing page. Collects email (required) and company (optional), persists to DB with async SQLAlchemy, sends confirmation via Resend, and enforces a 5-minute rate limit per email.

## Requirements

### R1: Waitlist Model and Storage

The system MUST persist waitlist entries with email (required, unique), company (optional), `created_at` timestamp, `source` defaulting to `"landing"`, and `tenant_id` (UUID FK to tenants, nullable for migration compatibility).
(Previously: No tenant_id field)

| Field      | Type         | Required | Unique | Default |
|------------|--------------|----------|--------|---------|
| email      | str          | Yes      | Yes    | —       |
| company    | str          | No       | No     | —       |
| created_at | datetime     | Yes      | No     | now()   |
| source     | str          | Yes      | No     | "landing" |
| tenant_id  | UUID FK      | No (null) | No    | —       |

#### Scenario: Successful insertion with tenant
- GIVEN a valid email with tenant context set by middleware
- WHEN the backend persists the entry
- THEN tenant_id is stored from the current tenant context

#### Scenario: Email missing
- GIVEN a request without an email field
- WHEN the backend attempts insertion
- THEN a validation error is raised

#### Scenario: Existing entry migration
- GIVEN waitlist entries existed before multi-tenant
- WHEN the migration runs
- THEN all existing entries have tenant_id set to "AUKALABS"

### R2: POST /api/v1/waitlist Endpoint

The system MUST expose `POST /api/v1/waitlist` accepting JSON `email` (required) and `company` (optional). MUST return 201 with the created entry on success.

#### Scenario: Happy path creation
- GIVEN a valid JSON body with email "new@example.com"
- WHEN POST /api/v1/waitlist is called
- THEN response is 201 with the entry data

#### Scenario: Invalid JSON body
- GIVEN a body with invalid structure
- WHEN POST /api/v1/waitlist is called
- THEN response is 422

### R3: Email Confirmation via Resend

The system MUST send a confirmation email via the Resend API after a waitlist entry is created.

#### Scenario: Confirmation sent
- GIVEN a new waitlist entry is persisted
- WHEN the backend calls the Resend API
- THEN a confirmation email is sent to the user's address

#### Scenario: Resend API failure
- GIVEN the Resend API returns an error
- WHEN the backend attempts to send
- THEN the waitlist entry is still persisted (fire-and-forget) and a warning is logged

### R4: Rate Limiting

The system MUST enforce a 5-minute cooldown per email using an in-memory cooldown dict. MUST return 429 with `retry-after` info when active.

#### Scenario: Cooldown active
- GIVEN "user@example.com" submitted 2 minutes ago
- WHEN the same email submits again
- THEN response is 429

#### Scenario: Cooldown expired
- GIVEN "user@example.com" submitted 6 minutes ago
- WHEN the same email submits again
- THEN submission succeeds (201)

### R5: Frontend Waitlist Form

The system MUST render a waitlist form between Pricing and Contact sections on the landing page. The form MUST include an email input (required) and company input (optional). MUST submit via POST to Next.js rewrite proxy `/api/backend/waitlist`.

#### Scenario: Form renders in correct position
- GIVEN the landing page loads
- WHEN the user scrolls through sections
- THEN the waitlist form appears between Pricing and Contact

#### Scenario: Successful frontend submission
- GIVEN the user enters a valid email and clicks submit
- WHEN the form POSTs to the proxy
- THEN a success message is displayed

### R6: Form Validation

The system MUST validate email format client-side (before submit) and server-side. MUST show inline error messages.

#### Scenario: Invalid email blocked client-side
- GIVEN the user types "bad-email"
- WHEN they attempt to submit
- THEN an inline error appears and the request is not sent

#### Scenario: Invalid email rejected server-side
- GIVEN a malformed email bypasses client checks
- WHEN POST /api/v1/waitlist is called
- THEN response is 422 with validation detail

### R7: Duplicate Prevention

The system MUST enforce a unique database constraint on the email column. MUST return 409 on duplicate.

#### Scenario: Duplicate email rejected
- GIVEN "existing@example.com" is already in the waitlist
- WHEN POST /api/v1/waitlist with the same email
- THEN response is 409 with duplicate error

### R8: Error Response Format

All error responses MUST be JSON with a `detail` field.

| Code | Condition | Response |
|------|-----------|----------|
| 422 | Invalid email | `{"detail": "Invalid email format"}` |
| 409 | Duplicate email | `{"detail": "Email already registered"}` |
| 429 | Rate limited | `{"detail": "Try again later"}` |
| 500 | Server error | `{"detail": "Internal server error"}` |

#### Scenario: Database unavailable
- GIVEN the database connection fails
- WHEN POST /api/v1/waitlist is called
- THEN response is 500 with JSON error body

#### Scenario: Missing Resend API key
- GIVEN RESEND_API_KEY is not set
- WHEN POST /api/v1/waitlist is called
- THEN the entry is still created (201) and email failure is logged
