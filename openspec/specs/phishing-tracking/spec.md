# Phishing Tracking Specification

## Purpose

Public, token-gated tracking endpoints: open pixel, click redirect, and path-based landing page with simulated credential capture (hash + discard). Every access records an `Event` for audit; tokens expire 7 days after campaign completion.

## Requirements

### Requirement: R1 Open Tracking Pixel

The system MUST expose public `GET /track/open/{token}.png` returning a 1×1 transparent pixel with no-cache headers, and MUST record an `open` Event for valid, non-expired tokens without requiring authentication.

#### Scenario: Valid token open

- GIVEN a target with a valid non-expired token
- WHEN the pixel is requested
- THEN a 1×1 image is returned and an `open` Event is recorded

#### Scenario: Unknown token

- GIVEN an unknown or expired token
- WHEN the pixel is requested
- THEN 404/410 is returned and no Event is recorded

### Requirement: R2 Click Tracking Redirect

The system MUST expose public `GET /track/click/{token}?url=...` recording a `click` Event and redirecting the visitor to the target's landing link. Unknown or expired tokens MUST NOT redirect and MUST NOT record an Event.

#### Scenario: Valid click

- GIVEN a target with a valid non-expired token
- WHEN the click URL is requested
- THEN a `click` Event is recorded and a 302 redirect to the landing link is returned

#### Scenario: Expired token click

- GIVEN an expired token
- WHEN the click URL is requested
- THEN 410 is returned and no redirect occurs

### Requirement: R3 Landing Page

The system MUST expose public `GET /l/{token}` rendering the campaign template's HTML with the target's substituted variables, including a warning that credential capture is simulated and an optional credential form.

#### Scenario: Render landing page

- GIVEN a target with a valid non-expired token
- WHEN `GET /l/{token}` is requested
- THEN the rendered HTML shows the substituted template with the simulated-capture notice and credential form

#### Scenario: Expired landing

- GIVEN an expired token
- WHEN `GET /l/{token}` is requested
- THEN 410 is returned

### Requirement: R4 Simulated Credential Capture

The system MUST, on credential form submission, compute a one-way SHA-256 hash of the submitted credentials, discard the plaintext (never persist it), and record a `credential` Event. The "credenciales" metric derives from these Events.

#### Scenario: Credential submission

- GIVEN a valid token and the landing form
- WHEN credentials are submitted
- THEN only a SHA-256 hash is persisted and a `credential` Event is recorded

#### Scenario: Plaintext never stored

- GIVEN a credential submission
- WHEN persisted data is inspected
- THEN no plaintext password exists anywhere in storage

### Requirement: R5 Token Expiry and Audit

The system MUST expire tracking tokens 7 days after the campaign's `completed_at`, returning 410 on use after expiry, and MUST record every access (open/click/landing) with metadata including IP and user-agent.

#### Scenario: Expiry window

- GIVEN a campaign completed 8 days ago
- WHEN any tracking endpoint is accessed with its token
- THEN 410 is returned

#### Scenario: Access audit metadata

- GIVEN a valid tracking access
- WHEN the recorded Event is inspected
- THEN metadata contains IP and user-agent

### Requirement: R6 Event Model

The system MUST persist `Event` rows with `campaign_id`, `target_id`, `type` in `open|click|report|credential`, `metadata` JSON, and `occurred_at`, indexed for results aggregation.

#### Scenario: Event recorded with type

- GIVEN a tracking action
- WHEN the Event row is created
- THEN type, campaign_id, target_id, and occurred_at are populated

#### Scenario: Events support aggregation

- GIVEN mixed open/click/credential actions on a campaign
- WHEN results query Events
- THEN per-type counts are derivable
