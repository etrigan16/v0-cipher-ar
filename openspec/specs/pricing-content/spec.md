# Pricing Content Specification

## Purpose

Define the pricing table display content for the landing page: three tiers (Free, Pro, Team) with dual-currency ARS+USD pricing and correct MVP feature sets per `wiki/projects/aukalabs/gtm-pricing.md`.

## Requirements

### Requirement: Tier Names and Prices

The pricing component SHALL display exactly three tiers with the following structure:

| Tier | Price (ARS) | Price (USD) |
|------|------------|-------------|
| Free | $0 | $0 |
| Pro | ARS 15k/mes | ~$15 USD/mes |
| Team | ARS 45k/mes | ~$45 USD/mes |

#### Scenario: Correct tier count and names

- GIVEN the pricing component renders
- WHEN the DOM is inspected for tier headings
- THEN exactly three tiers with names "Free", "Pro", and "Team" are present
- AND no tier named "Enterprise" or "ENTERPRISE" exists

#### Scenario: Free tier shows zero price

- GIVEN the Free tier card
- WHEN its price element is read
- THEN it displays "$0"
- AND it has no period label (no "/mes" suffix)

#### Scenario: Pro tier shows ARS primary with USD reference

- GIVEN the Pro tier card
- WHEN its price element is read
- THEN "ARS 15k/mes" is displayed as the primary price
- AND "~$15 USD" appears as a muted secondary reference

#### Scenario: Team tier shows ARS primary with USD reference

- GIVEN the Team tier card
- WHEN its price element is read
- THEN "ARS 45k/mes" is displayed as the primary price
- AND "~$45 USD" appears as a muted secondary reference

### Requirement: Feature Matrix

Each tier SHALL display a checklist of features per the MVP document. Included features show a check icon; excluded features show a minus icon.

| Tier | Included Features | Excluded Features |
|------|------------------|-------------------|
| Free | 1 activo monitoreado, Escaneo mensual de superficie, Simulación de phishing básica, Reportes por email | Alertas en tiempo real, API access, Soporte prioritario |
| Pro | Activos ilimitados, Escaneo continuo 24/7, Campañas de phishing ilimitadas, Alertas en tiempo real (Slack/Email/Webhook), API access, Dashboard avanzado con analytics | Soporte prioritario |
| Team | Todo lo de Pro, On-premise deployment, SSO / SAML, SLA personalizado, Soporte prioritario 24/7, Auditoría y compliance, Customer Success dedicado | (none) |

#### Scenario: Pro tier marked as popular

- GIVEN the Pro tier card
- WHEN its visual indicator is inspected
- THEN it has a "MÁS POPULAR" badge or border-highlight styling
- AND no other tier has the popular indicator

#### Scenario: Feature icons correct per tier

- GIVEN each tier's feature list
- WHEN the icon (check vs minus) for each feature is inspected
- THEN included features render a Check icon
- AND excluded features render a Minus icon
