```yaml
schema: gentle-ai.verify-result/v1
evidence_revision: sha256:d9e4fdef8938f2b89f045f73f9848ff4ce2dcb83938c063498cfec816ad8661d
verdict: pass
blockers: 0
critical_findings: 0
requirements: 10/10
scenarios: 19/19
test_command: pnpm test && cd backend && python -m pytest tests/ -q
test_exit_code: 0
test_output_hash: sha256:953be030b3f64d4fd4ef3315a815619528baeb4072e03f150de00eb6f1a54c0c
build_command: pnpm exec tsc --noEmit
build_exit_code: 0
build_output_hash: sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

## Verification Report

**Change**: attack-surface-core
**Version**: sprint-1-core (specs/attack-surface/spec.md)
**Mode**: Standard (no strict TDD gate)
**Verdict**: PASS (strict envelope + human assessment)

**Re-verify note**: This is the re-verification after remediation batch R. The prior report (evidence_revision `sha256:5038f3d1…`, verdict `fail`) flagged 1 PARTIAL scenario ("Dashboard counts reflect data") and 8 pre-existing frontend test failures. Both are now closed: `GET /asm/stats` + `api.asm.getStats()` + dashboard cards wired to real counts (with `app/dashboard/page.test.tsx` covering the scenario), and the MFA/login test failures fixed (`provisioning_uri` contract drift + login page R8 TOTP step).

### Completeness
| Metric | Value |
|--------|-------|
| Tasks total | 23 |
| Tasks complete | 23 |
| Tasks incomplete | 0 |

### Build & Tests Execution
**Build (type-check)**: ✅ Passed — `pnpm exec tsc --noEmit` exit 0 (empty output)
```text
exit 0, no diagnostics
```

**Lint**: ✅ 0 errors, 7 warnings (all pre-existing in untouched files: mfa page, auth-context, ui/carousel, ui/sidebar, use-mobile, hooks/use-mobile)

**Backend tests**: ✅ 58 passed / 2 skipped (RLS tests, PG-only per existing convention) — exit 0
```text
58 passed, 2 skipped, 3 warnings in 14.85s
```

**Frontend full suite**: ✅ 42 passed (8/8 files), 0 failures — exit 0
```text
Test Files  8 passed (8)
     Tests  42 passed (42)
```

**Coverage**: ➖ Not available (no coverage gate configured for this change)

### Spec Compliance Matrix
| Requirement | Scenario | Test | Result |
|-------------|----------|------|--------|
| Asset Model | Asset created for discovered host | `test_asm.py > TestAssetModel::test_asset_persists_all_fields`; `TestScanLifecycle::test_scan_created_and_completed` | ✅ COMPLIANT |
| Asset Model | Re-scan upserts instead of duplicating | `test_asm.py > TestAssetModel::test_rescan_upsert_no_duplicate`; `TestScanUpsert::test_rescan_no_duplicate_and_preserves_first_seen` | ✅ COMPLIANT |
| Scan Model | Scan lifecycle to complete | `test_asm.py > TestScanModel::test_scan_lifecycle_to_completed`; `TestScanLifecycle::test_scan_created_and_completed` | ✅ COMPLIANT |
| Scan Model | Scan errors recorded | `test_asm.py > TestScanError::test_discovery_failure_marks_scan_error` | ✅ COMPLIANT |
| Finding Model | Finding linked to asset and scan | `test_asm.py > TestFindingModel::test_finding_links_asset_and_scan`; `TestScanLifecycle::test_scan_created_and_completed` (results endpoint) | ✅ COMPLIANT |
| Trigger Scan | Valid domain scan | `test_asm.py > TestScanLifecycle::test_scan_created_and_completed` | ✅ COMPLIANT |
| Trigger Scan | Unauthenticated request rejected | `test_asm.py > TestUnauthenticated::test_invalid_token_rejected` | ✅ COMPLIANT |
| List Assets | Tenant sees own assets | `test_asm.py > TestIsolation::test_assets_isolated_between_tenants`; `TestAssetModel::test_asset_isolated_by_tenant` | ✅ COMPLIANT |
| List Assets | Another tenant isolated | `test_asm.py > TestIsolation::test_assets_isolated_between_tenants` (tenant B sees `[]`) | ✅ COMPLIANT |
| Scan Results | Results returned | `test_asm.py > TestScanLifecycle::test_scan_created_and_completed` (GET /asm/results); `test_missing_scan_404` | ✅ COMPLIANT |
| Scan Results | Cross-tenant scan denied | `test_asm.py > TestIsolation::test_cross_tenant_results_404` | ✅ COMPLIANT |
| Subdomain Enumeration (crt.sh) | crt.sh returns subdomains | `test_discovery.py > TestCrtShEnumeration::test_enumerates_and_dedupes_subdomains` (+ wildcard/leading-dot) | ✅ COMPLIANT |
| Subdomain Enumeration (crt.sh) | crt.sh unavailable | `test_discovery.py > TestCrtShEnumeration::test_crtsh_timeout_returns_partial`; `test_crtsh_http_error_returns_partial` | ✅ COMPLIANT |
| Active Fingerprinting | Host resolved and fingerprinted | `test_discovery.py > TestDnsResolution::test_resolves_a_and_aaaa`; `TestHttpTlsFingerprint::test_full_fingerprint_dict`; `TestScanLifecycle::test_scan_created_and_completed` (asset ip/port/service/fingerprint persisted) | ✅ COMPLIANT |
| Active Fingerprinting | Unresolvable host skipped | `test_discovery.py > TestDnsResolution::test_nxdomain_returns_empty`; `TestHttpTlsFingerprint::test_unreachable_host_never_raises` (drives orchestrator skip branch `if not result.ips: return`) | ✅ COMPLIANT |
| Multi-tenant RLS | RLS enabled on new tables | `test_multitenant.py` RLS tests (PG-gated, skip on SQLite per documented convention); `database.py::init_db` RLS block enables RLS + `tenant_isolation` policy on assets/scans/findings; `003_attack_surface.py` migration validated via `alembic upgrade head --sql` (PR 1 evidence) | ✅ COMPLIANT |
| Multi-tenant RLS | App filter proves isolation on SQLite | `test_asm.py > TestIsolation::test_assets_isolated_between_tenants`; `test_cross_tenant_results_404`; `TestAssetModel::test_asset_isolated_by_tenant` | ✅ COMPLIANT |
| Frontend Dashboard | Attack-surface shows real assets | `app/dashboard/attack-surface/page.test.tsx` (4 tests: lists assets, shows count, starts scan + refresh, error state); `lib/api.test.ts > describe("api.asm")` (4 contract tests) | ✅ COMPLIANT |
| Frontend Dashboard | Dashboard counts reflect data | `app/dashboard/page.test.tsx` (3 tests: real counts from /asm/stats, error fallback to zeros, loading placeholder); backend `test_asm.py > TestStats::test_stats_counts_only_own_tenant` + `test_stats_requires_auth`; `lib/api.test.ts > getStats` contract test | ✅ COMPLIANT |

**Compliance summary**: 19/19 scenarios compliant (previously 18/19, 1 partial)

### Correctness (Static Evidence)
| Requirement | Status | Notes |
|------------|--------|-------|
| Asset Model | ✅ Implemented | `models/asset.py`: CoercingUuid id, tenant FK NOT NULL, domain/subdomain/ip/port/service/fingerprint(Text JSON)/status/first_seen/last_seen; UniqueConstraint(tenant_id, domain, subdomain). `discovered_at` from spec not modeled (uses first_seen/last_seen; documented Phase-1 deviation) |
| Scan Model | ✅ Implemented | `models/scan.py`: id, tenant FK, domain, status (pending→running→completed/error), started_at, completed_at, created_at. Status verb `completed` vs spec `complete` (documented deviation, internally consistent) |
| Finding Model | ✅ Implemented | `models/finding.py`: id, tenant/asset/scan FKs, severity, title, detail, discovered_at |
| Trigger Scan | ✅ Implemented | `routes/asm.py` POST /asm/scans (body ScanCreate{domain}) → run_scan sync → {scan, assets}; auth via get_current_user |
| List Assets | ✅ Implemented | GET /asm/assets filtered by user.tenant_id |
| Scan Results | ✅ Implemented | GET /asm/results/{scan_id} tenant-filtered, else 404 |
| Subdomain Enumeration (crt.sh) | ✅ Implemented | `services/enumerate.py`: GET `?q=%25.{domain}&output=json`, dedupe, suffix-attack guard, partial-fail on timeout/error |
| Active Fingerprinting | ✅ Implemented | `services/dns.py` (dnspython A/AAAA, NXDOMAIN/NoAnswer tolerant) + `services/fingerprint.py` (httpx status/server/title/x-powered-by + ssl CN/SAN + candidate findings); orchestrated with config timeouts |
| Multi-tenant RLS | ✅ Implemented | `database.py` RLS ENABLE + tenant_isolation policy on assets/scans/findings; app-level filter in all /asm routes (SQLite isolation proof) |
| Frontend Dashboard | ✅ Implemented | `lib/api.ts` asm namespace (listAssets/scanDomain/getResults/getStats) + attack-surface page real fetch/scan; dashboard cards all wired to `api.asm.getStats()` (assets/findings/scans), phishing card static 0 (no counts endpoint for that domain — out of scope) |

### Coherence (Design)
| Decision | Followed? | Notes |
|----------|-----------|-------|
| POST /asm/scans with `{domain}` body (spec authoritative over stub) | ✅ Yes | ScanCreate{domain}; returns {scan, assets} |
| Upsert: composite unique + select-then-update preserving first_seen | ✅ Yes | Constraint is (tenant_id, domain, subdomain) — benign superset of design's (tenant_id, subdomain) |
| Synchronous in-route scan with bounded timeouts | ✅ Yes | config knobs dns_timeout/http_timeout/fingerprint_port/scheme consumed by run_scan |
| dnspython==2.8.0 pinned, per-query timeout | ✅ Yes | requirements.txt + dns.py QUERY_TIMEOUT |
| RLS PG-only + app filter on SQLite (tests skip) | ✅ Yes | Skip convention + app-level tenant_id filter |
| Finding source: fingerprint module returns candidates; orchestrator persists | ✅ Yes | fingerprint.findings → orchestrator Finding rows |
| `get_tenant_context` dep | ⚠️ Deviation | Used existing `get_current_user` (user.tenant_id) — documented, consistent with codebase |
| `services/discovery/` subpackage | ⚠️ Deviation | Implemented flat `services/enumerate.py|dns.py|fingerprint.py|orchestrator.py` — orchestrator-directed slice, documented |
| Frontend asm method names `list()/scan()/results()` | ⚠️ Deviation | Implemented `listAssets()/scanDomain()/getResults()/getStats()` — documented, matches backend DTOs |

### Issues Found
**CRITICAL**: None

**WARNING**: None (all previously-flagged warnings resolved)

**SUGGESTION**:
1. Asset model omits spec's `discovered_at` column (first_seen/last_seen cover it) — align spec text or add column in a follow-up.
2. Design's `get_tenant_context` shorthand resolved to existing `get_current_user` — document in design.md for future changes.
3. Discovery module path differs from design (`services/` flat vs `services/discovery/`) — update design.md so design and implementation agree.
4. `lib/api.ts` asm method names differ from design's `list()/scan(domain)/results(scanId)` — already self-consistent; note in design if kept.
5. Lint reports 7 pre-existing warnings in untouched files (mfa page, auth-context, ui/carousel, ui/sidebar, use-mobile) — cleanup candidate for a separate chore.
6. "Campañas de phishing" dashboard card stays static `0` — no counts endpoint exists for that domain; out of scope for this change.
7. Scan status verb `completed`/`pending` vs spec `complete`/`queued` — forward-compatible with Sprint-2 queue; consider aligning spec text.

### Verdict
PASS (strict envelope + human assessment). 23/23 tasks complete; 19/19 spec scenarios compliant with passing runtime coverage (backend 58 passed / 2 skipped, frontend 42/42, tsc clean, lint 0 errors). Remediation batch R closed the two prior failures: "Dashboard counts reflect data" is now COMPLIANT via `GET /asm/stats` + `TestStats` + `app/dashboard/page.test.tsx` + `api.asm.getStats()`; the 8 pre-existing MFA/login test failures are fixed (MFA `provisioning_uri` contract drift and the missing login TOTP step). No CRITICAL or WARNING findings remain. Archive readiness still requires the bounded review transaction (native status routes `nextRecommended: review`).
