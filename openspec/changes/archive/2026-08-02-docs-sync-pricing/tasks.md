# Tasks: Docs Sync — Pricing and Documentation Alignment

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 130–160 (tracked) / 190–250 (total with wiki) |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | ask-on-risk |

Decision needed before apply: Yes
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Pricing + README + config + wiki sync | Single PR | `git diff --stat` | `pnpm dev` visual review | `git checkout main -- components/pricing.tsx README.md openspec/config.yaml` |

---

## Phase 1: Pricing Component Rewrite

- [x] 1.1 Extend `PriceTier` type: add optional `usdNote: string` field in `components/pricing.tsx`
- [x] 1.2 Replace tier array: Free ($0), Pro (ARS 15k/mes ~$15 USD, popular), Team (ARS 45k/mes ~$45 USD, CTA "Contactar ventas" → `#contacto`)
- [x] 1.3 Update feature sets per spec feature matrix from `wiki/gtm-pricing.md`
- [x] 1.4 Add JSX render for `usdNote` muted text after price line and "MÁS POPULAR" badge on Pro

## Phase 2: README Rewrite

- [x] 2.1 Rewrite `README.md`: Title → Stack (Next.js 16, React 19, FastAPI, PostgreSQL) → Prerequisites → Quick Start → Tests → CI → Env Vars → Project Structure
- [x] 2.2 Add CI badge linking to GitHub Actions `quality` workflow with `pnpm test` and `cd backend && pytest` commands

## Phase 3: Config Fix & Wiki ADRs

- [x] 3.1 Fix `openspec/config.yaml` context line: "No CI" → "CI active (GitHub Actions workflow \`quality\` on push/PR to main)"
- [x] 3.2 Annotate ADR-002 as Superseded (Next.js 16 + React 19) in `wiki/projects/aukalabs/tech-decisions.md`
- [x] 3.3 Annotate ADR-007 as Superseded (Vercel deploy) in `wiki/projects/aukalabs/tech-decisions.md`
- [x] 3.4 Mark unimplemented ADRs as Deferred in `wiki/projects/aukalabs/tech-decisions.md`
- [x] 3.5 Update stack versions in `wiki/projects/aukalabs/plan-mvp.md`
- [x] 3.6 Update CI tracker from "Pending" to "Done" in `wiki/projects/aukalabs/sprint-0-foundation.md`

## Phase 4: Verification

- [x] 4.1 Manual visual review: three tiers rendered (Free/Pro/Team), ARS primary + USD muted, correct feature sets
- [x] 4.2 Manual check: "MÁS POPULAR" badge on Pro only, no Enterprise tier exists
- [x] 4.3 Manual pre-commit review: README accuracy (Next.js 16, React 19, CI badge, test commands)
- [x] 4.4 Visual diff: `openspec/config.yaml` context line changed correctly, no RegExp drift
