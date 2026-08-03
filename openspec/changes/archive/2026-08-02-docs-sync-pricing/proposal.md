# Proposal: Docs Sync — Pricing and Documentation Alignment

## Intent

Landing pricing and project docs are out of sync with MVP spec and actual codebase state. Pricing shows USD-only, wrong tiers/features, and stale Enterprise tier. README says Next.js 14 (reality 16), no CI (CI is live). Wiki ADRs describe unimplemented architectures. Align them to reduce confusion, avoid mispricing leads, and improve developer onboarding.

## Scope

### In Scope
- Rewrite `components/pricing.tsx`: 3 tiers (Free/Pro/Team), ARS+USD dual display, MVP feature matrix per gtm-pricing.md
- Rewrite `README.md`: real stack (Next.js 16, FastAPI, PostgreSQL), test/CI, env vars, quick start
- Fix `openspec/config.yaml`: context line "No CI" → "CI active (GitHub Actions workflow `quality` on push/PR to main)"
- Update 3 wiki/ files (gitignored): plan-mvp.md, tech-decisions.md, sprint-0-foundation.md
- Check `backend/.env.example`: RESEND_API_KEY already present — leave unchanged

### Out of Scope
- No new backend endpoints or pricing API
- No discount logic (annual/early/NGO/partner) in pricing component
- No feature toggles or gating logic (all features aspirational/marketing at this stage)
- No changes to waitlist form or contact section
- No changes to app/ pages beyond pricing component

## Capabilities

### New Capabilities
None — no new spec-level behavior introduced. Pure content/display sync.

### Modified Capabilities
None — existing spec behavior (waitlist, CI, auth, secret-config, test-infrastructure) unchanged.

## Approach

1. **pricing.tsx**: Replace tiers array with Free/Pro/Team. Add ARS primary display with muted USD parens (e.g., "ARS 15k/mes (~$15 USD)"). Update feature sets per gtm-pricing.md. Keep existing Tailwind/shadcn grid layout — content swap only.
2. **README.md**: Full rewrite with accurate stack, CI badge path, test commands, env setup, quick-start section, and `backend/.env.example` reference.
3. **openspec/config.yaml**: Single-line context edit.
4. **Wiki ADRs**: Mark ADR-002 (React 18+Vite) as superseded by Next.js 16+React 19. Mark ADR-007 (Docker→Render/Fly.io) as superseded by Vercel deploy. Mark unimplemented ADRs as deferred. Update Sprint 0 CI tracker.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `components/pricing.tsx` | Modified | Full rewrite: tiers, prices, features, dual-currency (~90-110 lines) |
| `README.md` | Modified | Full rewrite: stack, test/CI, env, quick start (~35-45 lines) |
| `openspec/config.yaml` | Modified | 1-line context fix |
| `wiki/projects/aukalabs/plan-mvp.md` | Modified | Sprint 0 status, stack versions (gitignored, ~30-40 lines) |
| `wiki/projects/aukalabs/tech-decisions.md` | Modified | ADR-002/ADR-007 superseded flags (gitignored, ~20-30 lines) |
| `wiki/projects/aukalabs/sprint-0-foundation.md` | Modified | CI tracker update (gitignored, ~10-15 lines) |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| ARS volatility makes USD equivalent outdated | Med | Use formulaic parenthetical; revisit pricing after beta feedback |
| README is GitHub-facing — stale info hurts onboarding | Low | Single-pass rewrite, review before commit |

## Rollback Plan

Revert tracked files via `git checkout main -- components/pricing.tsx README.md openspec/config.yaml`. Wiki files are gitignored — restore from local backup or re-edit manually.

## Dependencies

- MVP doc `wiki/projects/aukalabs/gtm-pricing.md` (authoritative feature/price source)
- `backend/.env.example` verified complete — no changes needed

## Success Criteria

- [ ] `components/pricing.tsx` shows Free/Pro/Team with ARS+USD dual display and correct MVP features
- [ ] `README.md` reflects actual stack (Next.js 16, React 19, FastAPI), CI pipeline, test commands, and env setup
- [ ] `openspec/config.yaml` context says "CI active" not "No CI"
- [ ] Wiki ADRs mark stale entries (ADR-002, ADR-007) as superseded
- [ ] Sprint 0 CI tracker updated to "Done"
