# Design: Docs Sync — Pricing and Documentation Alignment

## Technical Approach

Straightforward content swap across four disjoint areas. The pricing component keeps its existing shadcn/ui grid layout and module-private tier array, but with a new three-tier structure (Free/Pro/Team), dual-currency ARS+USD display, and the MVP feature matrix. README.md is a full rewrite. Wiki ADRs in `tech-decisions.md` get status annotations (Superseded / Deferred). `openspec/config.yaml` gets a single-line edit. No architectural changes, no new runtime interfaces, no data-flow modifications.

## Architecture Decisions

### Decision: Pricing Data Model

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Extend inline tier array with `usdNote` field | Keeps module-private type; no API dependency; matches all other section components (hero, faq, services) | **Chosen** |
| External data source / API-driven | Overengineered — no pricing API exists; all features are aspirational/marketing at this stage | Rejected |

**Choice**: Add optional `usdNote: string` to each tier object for the muted secondary price.

### Decision: Team Tier Positioning

**Choice**: Enterprise → Team at fixed price (ARS 45k/mes / ~$45 USD) in the third column, with CTA "Contactar ventas" pointing to the contact section.

**Rationale**: Enterprise "Custom" pricing was inconsistent with MVP Go-To-Market targeting Argentine SMBs. Team at fixed price aligns with product positioning and eliminates friction for the target buyer.

### Decision: README Structure

**Choice**: Title → Stack → Prerequisites → Quick Start → Tests → CI → Env Vars → Project Structure → Contributing. CI badge links to GitHub Actions `quality` workflow.

**Rationale**: Full onboarding structure reduces developer friction. The current 18-line README lacks test commands, CI presence, or env setup instructions.

### Decision: ADR Annotation Strategy

**Choice**: Preserve original ADR text verbatim and add `Status: Superseded | Deferred` annotations. Do not delete or rewrite.

**Rationale**: Preserves audit trail. Future readers see both the original intent and the superseding reality.

## Data Flow

N/A — no runtime data-flow changes. Pricing data moves from static tier array → React render → DOM. README and ADRs are static markdown consumed at read time.

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `components/pricing.tsx` | Modify | Replace tiers array with Free/Pro/Team; add `usdNote` field and its JSX render; update descriptions, CTAs, feature lists per spec |
| `README.md` | Modify | Full rewrite (~45-55 lines) with accurate stack, CI badge, test commands, env setup |
| `openspec/config.yaml` | Modify | Line 8: `No CI` → `CI active (GitHub Actions workflow \`quality\` on push/PR to main)` |
| `wiki/projects/aukalabs/tech-decisions.md` | Modify | ADR-002 → Superseded (Next.js 16 + React 19); ADR-007 → Superseded (Vercel deploy); unimplemented ADRs → Deferred (gitignored) |
| `wiki/projects/aukalabs/plan-mvp.md` | Modify | Stack version updates, pricing section alignment (gitignored) |
| `wiki/projects/aukalabs/sprint-0-foundation.md` | Modify | CI tracker → "Done" with GitHub Actions quality workflow reference (gitignored) |

## Interfaces / Contracts

No new TypeScript exports. The existing module-private tier type is extended inline:

```typescript
type PriceTier = {
  name: string            // "Free" | "Pro" | "Team"
  price: string           // ARS primary: "ARS 15k" | "ARS 45k" | "$0"
  usdNote?: string        // muted secondary: "~$15 USD" | "~$45 USD"
  period?: string         // "/mes" for paid tiers only
  desc: string
  popular?: boolean       // true only for Pro
  features: { included: boolean; text: string }[]
  cta: string
  href: string
}
```

The USD note renders after the main price line in the existing flex container:

```tsx
<span className="font-mono text-4xl font-bold">{tier.price}</span>
{tier.period && <span className="font-mono text-sm text-muted-foreground">{tier.period}</span>}
{tier.usdNote && <p className="font-mono text-xs text-muted-foreground/60 mt-0.5">{tier.usdNote}</p>}
```

Component export name `PricingSection` stays unchanged — no import edits in `app/page.tsx`.

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Visual | Three tiers rendered, ARS primary + USD muted, correct features | Manual visual review in dev server |
| Visual | "MÁS POPULAR" badge on Pro only | Manual visual check |
| Docs | README accuracy (stack, CI badge, commands) | Manual pre-commit review |
| Config | openspec/config.yaml context line | Visual diff — single-line change |

No new automated tests. The component is purely presentational with no interactive logic. All features are aspirational/marketing labels — no gating or backend integration exists yet. If interactive tier selection or checkout is added later, unit tests should be introduced at that point.

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary. The change touches static content (React component markup, markdown, YAML) only.

## Migration / Rollout

No migration required. All changes are content swaps that take effect on the next Vercel deploy. Wiki changes (gitignored) take effect on next `git push`. Rollback: `git checkout main -- components/pricing.tsx README.md openspec/config.yaml`; wiki files restored from local copy.

## Open Questions

None — all scope decisions were approved by the user.
