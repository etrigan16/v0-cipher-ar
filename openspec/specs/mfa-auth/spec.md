# MFA Authentication Specification

## Purpose

Optional TOTP-based multi-factor authentication (Google Authenticator-compatible via pyotp). Two-step login with 5-minute partial tokens.

## Requirements

### R1: MFA User Fields

The User model MUST add `mfa_secret` (nullable String) and `mfa_enabled` (Boolean, default False).

- GIVEN a migration applies new columns | WHEN existing users are queried | THEN `mfa_secret = NULL` AND `mfa_enabled = False`
- GIVEN a new user registers | WHEN the user record is created | THEN `mfa_secret = NULL` AND `mfa_enabled = False`

### R2: POST /auth/mfa/setup

The system MUST provide an authenticated endpoint generating a new TOTP secret and provisioning URI.

- GIVEN an authenticated user with a full JWT | WHEN POST /auth/mfa/setup is called | THEN the response MUST include `secret` (base32) AND `provisioning_uri` (otpauth://)
- GIVEN MFA is already enabled | WHEN setup is called | THEN the secret MUST be regenerated AND MFA MUST remain disabled until verify
- GIVEN a partial token is used | WHEN setup is called | THEN 401 MUST be returned

### R3: POST /auth/mfa/verify

The system MUST provide an endpoint to confirm a TOTP code and enable MFA.

- GIVEN a user who called setup | WHEN a valid 6-digit TOTP is submitted | THEN `mfa_enabled = True` AND success is confirmed
- GIVEN a user who called setup | WHEN an invalid TOTP is submitted | THEN 400 MUST be returned AND `mfa_enabled` stays False
- GIVEN a user who has NOT called setup | WHEN verify is called | THEN 400 MUST be returned

### R4: POST /auth/mfa/disable

The system MUST provide an endpoint to disable MFA with password confirmation.

- GIVEN MFA is enabled | WHEN the correct password is submitted | THEN `mfa_enabled = False` AND `mfa_secret` is cleared
- GIVEN MFA is enabled | WHEN an incorrect password is submitted | THEN 401 MUST be returned AND MFA stays enabled
- GIVEN MFA is already disabled | WHEN disable is called | THEN 400 MUST be returned

### R5: POST /auth/mfa/challenge

The system MUST provide a public endpoint exchanging a partial token + valid TOTP for a full JWT.

- GIVEN a valid partial token + correct TOTP | WHEN challenge is called | THEN a full JWT (`access_token`, 1440 min) MUST be returned
- GIVEN a valid partial token + incorrect TOTP | WHEN challenge is called | THEN 401 MUST be returned
- GIVEN an expired partial token | WHEN challenge is called | THEN 401 MUST be returned
- GIVEN a full JWT (not partial) | WHEN challenge is called | THEN 400 MUST be returned

### R6: Login Flow Modification

The login endpoint MUST return a partial token when MFA is enabled and a full token otherwise. `get_current_user` MUST reject partial tokens.

- GIVEN valid credentials + MFA disabled | WHEN login is called | THEN `access_token` MUST be returned WITHOUT `partial_token` or `mfa_required`
- GIVEN valid credentials + MFA enabled | WHEN login is called | THEN `partial_token` + `mfa_required: true` MUST be returned WITHOUT `access_token`
- GIVEN a partial token | WHEN `get_current_user` validates it | THEN 401 MUST be returned

### R7: Frontend MFA Setup Page

The system MUST provide a `/dashboard/mfa` page for MFA management.

- GIVEN an authenticated user on /dashboard/mfa | WHEN the page loads | THEN a QR code from setup MUST be displayed WITH a TOTP input for verification
- GIVEN MFA is enabled | WHEN viewing /dashboard/mfa | THEN a "Disable MFA" button WITH password confirmation MUST be shown
- GIVEN verification succeeds | WHEN the user enters a valid TOTP code | THEN "MFA Enabled" status MUST be displayed

### R8: Frontend Login TOTP Step

The login page MUST show a conditional TOTP step when `mfa_required` is true.

- GIVEN the login response includes `mfa_required: true` | WHEN the client receives it | THEN a TOTP input MUST appear AND email/password fields MUST be disabled
- GIVEN a valid TOTP code on the challenge step | WHEN challenge succeeds | THEN the full JWT MUST be stored as the session token
- GIVEN an invalid TOTP code | WHEN challenge fails | THEN an error message MUST be shown AND the user MAY retry

### R9: Challenge Rate Limiting

The `/auth/mfa/challenge` endpoint MUST limit attempts to 5 per minute per IP or partial token.

- GIVEN more than 5 attempts per minute | WHEN a new attempt is made | THEN 429 MUST be returned
- GIVEN the rate limit was exceeded | WHEN 1 minute elapses | THEN attempts MUST be accepted again

### R10: Backward Compatibility

Non-MFA users MUST see zero change in the auth flow.

- GIVEN a user without MFA | WHEN they log in | THEN the flow MUST be identical to pre-MFA behavior
- GIVEN an existing JWT issued before MFA deploy | WHEN used with /auth/me | THEN it MUST remain valid
