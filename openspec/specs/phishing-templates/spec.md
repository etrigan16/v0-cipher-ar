# Phishing Templates Specification

## Purpose

Tenant-owned phishing email templates: model, tenant-scoped CRUD, 8 seeded templates across bank/government/tech categories, variable substitution rendering (`{{nombre}}`, `{{empresa}}`, `{{link}}`), and a structured frontend editor with preview. No drag-drop dependency.

## Requirements

### Requirement: R1 Template Model

The system MUST persist `Template` rows with `tenant_id` (FK), `name`, `subject`, `html_body`, and `category` (`bank|government|tech`), following repo conventions (`CoercingUuid`, `ix_*_tenant_id` index, `server_default=func.now()`), with RLS enabled on the table.

#### Scenario: Create template

- GIVEN an authenticated tenant
- WHEN the tenant creates a template with name, subject, html_body, and category
- THEN a Template row persists with the tenant's `tenant_id` and default timestamps

#### Scenario: Cross-tenant visibility

- GIVEN a template belonging to tenant B
- WHEN tenant A queries templates
- THEN tenant B's template is absent from results

### Requirement: R2 Template CRUD Endpoints

The system MUST expose tenant-scoped `GET/POST /phishing/templates` and `GET/PUT/DELETE /phishing/templates/{id}` protected by `get_current_user`; unknown or cross-tenant ids MUST return 404.

#### Scenario: Create and list

- GIVEN an authenticated tenant
- WHEN POST creates a template and GET lists templates
- THEN the created template appears in the list

#### Scenario: Update own template

- GIVEN a template owned by the tenant
- WHEN PUT changes subject and html_body
- THEN the persisted values reflect the update

#### Scenario: Cross-tenant or unknown id

- GIVEN a template id of another tenant or a nonexistent id
- WHEN GET/PUT/DELETE `/phishing/templates/{id}` is called
- THEN 404 is returned with no data leak

### Requirement: R3 Seeded Templates

The system MUST seed 8 templates (bank/government/tech) in migration `005_phishing`, each with `subject` and `html_body` containing `{{nombre}}`, `{{empresa}}`, and `{{link}}` variables, available to every tenant.

#### Scenario: Seeds present

- GIVEN a fresh database after migration 005
- WHEN a tenant lists templates
- THEN 8 seed templates are available with valid subject and html_body

#### Scenario: Seed variables

- GIVEN a seed template
- WHEN it is inspected
- THEN all three variables appear in subject or html_body

### Requirement: R4 Variable Substitution

The system MUST render template `subject`/`html_body` by replacing `{{nombre}}`, `{{empresa}}`, and `{{link}}` with per-target values. The renderer MUST escape target-supplied values to prevent HTML injection, and MUST render gracefully when a variable value is missing.

#### Scenario: All variables substituted

- GIVEN a template with the three variables and a target with name, company, and link
- WHEN rendering runs
- THEN every variable is replaced with the target's value

#### Scenario: Missing variable value

- GIVEN a template referencing a variable the target lacks
- WHEN rendering runs
- THEN rendering completes without error and the placeholder renders empty

#### Scenario: HTML escaping

- GIVEN a target name containing `<script>` markup
- WHEN rendering runs
- THEN the markup is escaped and not executed as HTML

### Requirement: R5 Structured Editor

The frontend MUST provide a structured template editor with: subject input, HTML body textarea, variable insertion chips (`{{nombre}}`, `{{empresa}}`, `{{link}}`), live preview rendered with sample data, and an HTML source toggle.

#### Scenario: Insert variable

- GIVEN the editor open
- WHEN the user clicks a variable chip
- THEN the placeholder is inserted at the cursor in the body

#### Scenario: Preview with sample data

- GIVEN a template with variables
- WHEN the user toggles preview
- THEN the rendered body shows sample values substituted for the variables

#### Scenario: Source toggle round-trip

- GIVEN the editor open
- WHEN the user toggles to source view, edits the raw html_body, and saves
- THEN the persisted html_body matches the edited source
