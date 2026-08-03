# Secret Configuration Specification

## Purpose

Remove hardcoded secrets and recipients: the backend requires `SECRET_KEY` from the environment, and the contact endpoint resolves its recipient from `CONTACT_EMAIL`. No default secret or default recipient may remain.

## Requirements

### Requirement: Required SECRET_KEY

`backend/app/config.py` MUST load `SECRET_KEY` from the environment with no default value. The backend MUST fail to start when `SECRET_KEY` is unset and MUST start normally when it is set.

#### Scenario: Boot fails without SECRET_KEY

- GIVEN `SECRET_KEY` is not set in the environment
- WHEN the backend starts
- THEN startup fails with a clear error naming `SECRET_KEY`

#### Scenario: Boot succeeds with SECRET_KEY

- GIVEN `SECRET_KEY` is set in the environment
- WHEN the backend starts
- THEN the app boots and serves requests

### Requirement: Env-Driven Contact Recipient

`app/api/send/route.ts` MUST read the email recipient from `CONTACT_EMAIL` and MUST NOT use a hardcoded address. When `CONTACT_EMAIL` is unset, the endpoint MUST NOT send email and MUST respond with HTTP 500; no fallback recipient is used, consistent with the no-default hardening decision.

#### Scenario: Contact form delivers to configured address

- GIVEN `CONTACT_EMAIL` and `RESEND_API_KEY` are set
- WHEN the contact form POSTs valid data
- THEN Resend sends to the `CONTACT_EMAIL` address and the endpoint responds success

#### Scenario: Missing CONTACT_EMAIL blocks send

- GIVEN `CONTACT_EMAIL` is unset
- WHEN the contact form POSTs valid data
- THEN no email is sent and the endpoint responds with HTTP 500

### Requirement: Documented Env Vars

`backend/.env.example` MUST document `SECRET_KEY` and `CONTACT_EMAIL` as required variables.

#### Scenario: Example env is accurate

- GIVEN the backend example env file
- WHEN it is inspected
- THEN it lists `SECRET_KEY` and `CONTACT_EMAIL` with required markers
