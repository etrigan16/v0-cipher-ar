## Exploration: docs-sync-pricing

### Current State

The landing page's `components/pricing.tsx` shows three tiers: **Free** ($0), **Pro** ($99/mes), and **Enterprise** (Custom). The MVP document at `wiki/projects/aukalabs/gtm-pricing.md` specifies Free ($0), **Pro (ARS 15k/mes ≈ $15 USD)**, and **Team (ARS 45k/mes ≈ $45 USD)** — a different enterprise tier name, completely different pricing, and ARS-only billing with optional USD reference.

Separately, the project's documentation is significantly out of date:
- **README.md (tracked)**: Says Next.js 14, no tests/CI, SECRET_KEY default — reality is Next.js 16.2.4, React 19, vitest+pytest+CI pipeline all active, `.env.example` requires explicit SECRET_KEY.
- **wiki/projects/aukalabs/plan-mvp.md (gitignored)**: Describes Sprint 0 as ongoing, stack as React 18+Vite — actual Sprint 0 is complete (CI, auth, waitlist, landing all done), stack is Next.js 16+React 19+Tailwind 4.
- **wiki/projects/aukalabs/tech-decisions.md (gitignored)**: 12 ADRs, mostly intent-only. ADR-002 says React 18+Vite (should be Next.js 16+React 19), ADR-007 says Docker→Render/Fly.io (actual deploy uses Vercel).
- **wiki/projects/aukalabs/sprint-0-foundation.md (gitignored)**: CI tracker still shows "Pending" — CI pipeline is completed and archived.

### Affected Areas

- `components/pricing.tsx` — Full rewrite needed: 3 tiers, prices, features, currency display (tracked, ~136 lines)
- `README.md` — Full rewrite needed: stack version, test/CI presence, env vars (tracked, ~18 lines)
- `wiki/projects/aukalabs/plan-mvp.md` — Update Sprint 0 status, stack version, CI status (gitignored)
- `wiki/projects/aukalabs/tech-decisions.md` — Update ADR-002 (React 18→Next.js 16/React 19), ADR-007 (deploy target) (gitignored)
- `wiki/projects/aukalabs/sprint-0-foundation.md` — Update CI tracker to reflect completion (gitignored)
- `openspec/config.yaml` — Context line says "No CI" — should be updated to reflect actual state (tracked)

### Pricing Comparison

| Dimension | Landing (current) | MVP doc (target) | Delta |
|-----------|------------------|-------------------|-------|
| Tier names | Free / Pro / Enterprise | Free / Pro / Team | Enterprise→Team rename |
| Pro price | $99/mes USD | ARS 15k/mes ($15 USD) | -84% price change + currency shift |
| Team/Enterprise | "Custom" (contact sales) | ARS 45k/mes ($45 USD) | Fixed pricing, not custom |
| Currency | USD only | ARS primary, USD secondary | Dual-currency required |
| Feature set | 7 features/tier (checklist) | 11 features/tier (table grid) | Very different feature matrix |
| Discounts | None | 4 discount types (annual, early, NGO, partner) | Not in pricing component |
| Description | Spanish | Spanish | Same language, different copy |
| CTA | "Comenzar gratis" / "Empezar prueba gratuita" / "Contactar ventas" | "Comenzar gratis" / "Empezar prueba gratuita" / "Contactar ventas" | Similar |

### Approaches

1. **Full pricing alignment** — Rewrite `pricing.tsx` to match gtm-pricing.md exactly
   - Pros: Exact match with MVP doc, correct pricing for target market
   - Cons: Loses USD-only simplicity; Enterprise→Team rename may affect other pages
   - Effort: Medium (~80-100 tracked lines changed in pricing.tsx)

2. **Dual-currency pricing display** — Show both ARS (primary) and USD (secondary/muted) per tier
   - Pros: Serves both local and international audiences per ADR-008
   - Cons: More visual complexity, no precedent in current UI
   - Effort: Medium (~100-120 tracked lines)

3. **Feature parity with ARS focus** — Align features and tier names, show ARS, mention USD on hover/tooltip
   - Pros: Clean UI, targets primary audience (Argentine SMBs)
   - Cons: Hides USD, international users may be confused
   - Effort: Medium (~80-100 tracked lines)

### Docs Approach

| Doc | Tracked? | Lines | Approach |
|-----|----------|-------|----------|
| README.md | Yes | ~18→50 | Full rewrite: stack versions, test/CI, env requirements |
| plan-mvp.md | No (wiki/) | ~159 | Update Sprint 0 status, stack versions, CI tracker |
| tech-decisions.md | No (wiki/) | ~241 | Update ADR-002 (React 18→Next.js 16), ADR-007 (deploy target) |
| sprint-0-foundation.md | No (wiki/) | ~282 | Update CI tracker to "Done", add waitlist-api completion |
| openspec/config.yaml | Yes | ~37 | Fix "No CI" context line (one-line edit) |

### Effort/Lines Forecast

| Category | Tracked (review-budget) | Untracked (wiki, gitignored) |
|----------|------------------------|------------------------------|
| Pricing component | ~80-100 lines | — |
| README.md | ~35-45 lines | — |
| openspec/config.yaml | ~1 line | — |
| Wiki docs (3 files) | — | ~40-50 lines |
| **Total** | **~116-146 lines** | **~40-50 lines** |

**Review budget risk**: LOW — ~116-146 tracked lines is well under the 400-line default threshold and the 800-line session budget.

### Risks

- **Pricing accuracy**: ARS is volatile. Using fixed ARS 15k/45k may become misaligned with USD equivalent over time. Recommend revisiting pricing strategy after beta feedback.
- **Feature matrix redesign**: The current checklist per-tier (7 features) vs MVP table (11 features with different granularity) means the component structure changes significantly — not just a text edit.
- **README visibility**: README is shown on GitHub repo front page. Stale info affects developer onboarding. Low risk but high visibility.
- **No `.github/workflows/ci.yml` in glob results**: CI workflow exists on disk but was not found by initial glob (`.github/` is a hidden directory). Confirmed present at `.github/workflows/ci.yml`.

### Ready for Proposal

**Yes** — exploration is complete. The scope is clear and bounded. Tracked changes are ~116-146 lines (low budget risk). Recommend starting with **sdd-propose** (hybrid mode), specifying which pricing approach to take, and which docs to update. The user should decide: (1) dual-currency or ARS-only, (2) how to handle the Enterprise→Team rename, and (3) how much README rewrite depth.
