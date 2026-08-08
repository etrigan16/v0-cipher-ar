"""Phase 1 (Data Foundation) tests for the attack-surface models.

These run on SQLite (via conftest) and prove:
- ``Asset``, ``Scan``, ``Finding`` persist and read back correctly.
- The composite unique ``(tenant_id, domain, subdomain)`` on ``Asset``
  prevents duplicate rows, which is the key that lets a re-scan *upsert*
  without producing duplicates (preserving ``first_seen`` happens in the
  discovery orchestrator, PR 3).

Selective run: ``pytest tests/test_asm.py -k upsert``
"""

import datetime

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.asset import Asset
from app.models.finding import Finding
from app.models.scan import Scan
from app.models.tenant import Tenant

# Phase 3: orchestrator module is patched so tests never touch the network.
from app.services import orchestrator  # noqa: E402


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with Session() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def tenant(db_session: AsyncSession):
    t = Tenant(name="Acme Corp", slug="acme-corp")
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)
    return t


class TestAssetModel:
    """Asset: CoercingUuid id, tenant FK, domain/subdomain/ip/port/service/fingerprint/status/timestamps."""

    async def test_asset_persists_all_fields(self, db_session: AsyncSession, tenant):
        """R-Asset: A discovered host persists with populated fields."""
        asset = Asset(
            tenant_id=tenant.id,
            domain="example.com",
            subdomain="www.example.com",
            ip="93.184.216.34",
            port=443,
            service="https",
            fingerprint='{"title": "Example", "server": "ECS"}',
            status="discovered",
        )
        db_session.add(asset)
        await db_session.commit()
        await db_session.refresh(asset)

        assert asset.id is not None
        assert asset.tenant_id == tenant.id
        assert asset.domain == "example.com"
        assert asset.subdomain == "www.example.com"
        assert asset.ip == "93.184.216.34"
        assert asset.port == 443
        assert asset.service == "https"
        assert asset.first_seen is not None
        assert asset.last_seen is not None
        assert asset.status == "discovered"

    async def test_rescan_upsert_no_duplicate(self, db_session: AsyncSession, tenant):
        """R-Asset/Upsert: Inserting the same (tenant, domain, subdomain) twice raises — no dupes."""
        t_id = tenant.id  # capture before any rollback expires the instance
        common = dict(tenant_id=t_id, domain="example.com", subdomain="api.example.com")
        first = Asset(**common, ip="203.0.113.1")
        db_session.add(first)
        await db_session.commit()

        # Simulated re-scan of the same subdomain: updating last_seen is the
        # orchestrator's job (PR 3); the DB constraint here must reject a
        # second insert, guaranteeing re-scan cannot create a duplicate row.
        duplicate = Asset(**common, ip="203.0.113.1")
        db_session.add(duplicate)
        with pytest.raises(Exception):
            await db_session.commit()
        await db_session.rollback()

        rows = (
            await db_session.execute(
                select(Asset).where(
                    Asset.tenant_id == t_id,
                    Asset.domain == "example.com",
                    Asset.subdomain == "api.example.com",
                )
            )
        ).scalars().all()
        assert len(rows) == 1
        assert rows[0].id == first.id

    async def test_asset_isolated_by_tenant(self, db_session: AsyncSession, tenant):
        """R-Isolation: Assets belonging to another tenant are not visible on this tenant."""
        other = Tenant(name="Other Inc", slug="other-inc")
        db_session.add(other)
        await db_session.commit()
        await db_session.refresh(other)

        db_session.add(
            Asset(tenant_id=other.id, domain="other.com", subdomain="other.com")
        )
        await db_session.commit()

        mine = (
            await db_session.execute(
                select(Asset).where(Asset.tenant_id == tenant.id)
            )
        ).scalars().all()
        assert len(mine) == 0

    async def test_risk_score_nullable_then_settable(self, db_session: AsyncSession, tenant):
        """R-Asset/004: legacy assets read back with NULL risk_score; scan sets it."""
        asset = Asset(
            tenant_id=tenant.id, domain="example.com", subdomain="www.example.com"
        )
        db_session.add(asset)
        await db_session.commit()
        await db_session.refresh(asset)

        # Legacy row persisted before migration 004 -> NULL until a scan recomputes.
        assert asset.risk_score is None

        asset.risk_score = 7.5
        await db_session.commit()
        await db_session.refresh(asset)
        assert asset.risk_score == 7.5


class TestScanModel:
    """Scan: id, tenant FK, domain, status lifecycle, started/completed/created timestamps."""

    async def test_scan_persists_pending(self, db_session: AsyncSession, tenant):
        scan = Scan(tenant_id=tenant.id, domain="example.com")
        db_session.add(scan)
        await db_session.commit()
        await db_session.refresh(scan)

        assert scan.id is not None
        assert scan.tenant_id == tenant.id
        assert scan.domain == "example.com"
        assert scan.status == "pending"
        assert scan.created_at is not None
        assert scan.started_at is None
        assert scan.completed_at is None

    async def test_scan_lifecycle_to_completed(self, db_session: AsyncSession, tenant):
        scan = Scan(tenant_id=tenant.id, domain="example.com", status="running")
        scan.started_at = datetime.datetime.now(datetime.timezone.utc)
        db_session.add(scan)
        await db_session.commit()

        scan.status = "completed"
        scan.completed_at = datetime.datetime.now(datetime.timezone.utc)
        await db_session.commit()
        await db_session.refresh(scan)

        assert scan.status == "completed"
        assert scan.completed_at >= scan.started_at


class TestFindingModel:
    """Finding: id, tenant/asset/scan FK, severity, title, detail, discovered_at."""

    async def test_finding_links_asset_and_scan(
        self, db_session: AsyncSession, tenant
    ):
        asset = Asset(
            tenant_id=tenant.id, domain="example.com", subdomain="www.example.com"
        )
        scan = Scan(tenant_id=tenant.id, domain="example.com", status="completed")
        db_session.add_all([asset, scan])
        await db_session.commit()
        await db_session.refresh(asset)
        await db_session.refresh(scan)

        finding = Finding(
            tenant_id=tenant.id,
            asset_id=asset.id,
            scan_id=scan.id,
            severity="medium",
            title="Missing HSTS header",
            detail="The host does not send Strict-Transport-Security.",
        )
        db_session.add(finding)
        await db_session.commit()
        await db_session.refresh(finding)

        assert finding.id is not None
        assert finding.tenant_id == tenant.id
        assert finding.asset_id == asset.id
        assert finding.scan_id == scan.id
        assert finding.severity == "medium"
        assert finding.title == "Missing HSTS header"
        assert finding.discovered_at is not None

    async def test_new_columns_default_safely(self, db_session: AsyncSession, tenant):
        """R-Finding/004: a pre-scoring finding reads back NULL risk fields + status open."""
        asset = Asset(
            tenant_id=tenant.id, domain="example.com", subdomain="www.example.com"
        )
        scan = Scan(tenant_id=tenant.id, domain="example.com", status="completed")
        db_session.add_all([asset, scan])
        await db_session.commit()
        await db_session.refresh(asset)
        await db_session.refresh(scan)

        finding = Finding(
            tenant_id=tenant.id,
            asset_id=asset.id,
            scan_id=scan.id,
            severity="medium",
            title="Missing HSTS header",
            detail="The host does not send Strict-Transport-Security.",
        )
        db_session.add(finding)
        await db_session.commit()
        await db_session.refresh(finding)

        # No backfill: risk/enrichment columns stay NULL, status defaults to open.
        assert finding.status == "open"
        assert finding.risk_score is None
        assert finding.risk_level is None
        assert finding.finding_type is None
        assert finding.remediation is None
        assert finding.enriched_at is None

    async def test_finding_persists_scored_fields(self, db_session: AsyncSession, tenant):
        """R-Finding/004: scored findings round-trip all risk columns."""
        asset = Asset(
            tenant_id=tenant.id, domain="example.com", subdomain="www.example.com"
        )
        scan = Scan(tenant_id=tenant.id, domain="example.com", status="completed")
        db_session.add_all([asset, scan])
        await db_session.commit()
        await db_session.refresh(asset)
        await db_session.refresh(scan)

        finding = Finding(
            tenant_id=tenant.id,
            asset_id=asset.id,
            scan_id=scan.id,
            severity="high",
            title="Expired TLS certificate",
            detail="The certificate expired.",
            finding_type="tls-expired",
            risk_score=9.5,
            risk_level="critical",
            remediation="Renew the certificate before it expires.",
            status="open",
        )
        db_session.add(finding)
        await db_session.commit()
        await db_session.refresh(finding)

        assert finding.finding_type == "tls-expired"
        assert finding.risk_score == 9.5
        assert finding.risk_level == "critical"
        assert finding.remediation == "Renew the certificate before it expires."
        assert finding.status == "open"


# ---------------------------------------------------------------------------
# Phase 3: Orchestration + API integration tests (PR 3)
# ---------------------------------------------------------------------------
# These exercise the real /asm routes over the SQLite ASGITransport client,
# with the external discovery services mocked via monkeypatch on the
# orchestrator module. They prove the scan lifecycle, Asset upsert on
# re-scan, cross-tenant isolation (app-level filter), and error status.


class _FakeResolution:
    """Stand-in for a DiscoveryResult: has .ips/.hostname/.cname."""

    def __init__(self, ips, cname=None):
        self.ips = ips
        self.cname = cname
        self.hostname = "www.example.com"


def _fingerprint(**overrides) -> dict:
    """Build a fingerprint dict; the default fires the 3 missing-header rules."""
    fp = {
        "hostname": "www.example.com",
        "port": 443,
        "scheme": "https",
        "status_code": 200,
        "title": "Example",
        "server": "nginx",
        "x_powered_by": None,
        "strict_transport_security": None,
        "x_content_type_options": None,
        "content_security_policy": None,
        "set_cookie": None,
        "tls": {
            "subject_cn": "*.example.com",
            "issuer_cn": "Let's Encrypt",
            "subject_alt_names": ["example.com"],
            "not_before": "2026-01-01T00:00:00Z",
            "not_after": "2027-01-01T00:00:00Z",
        },
    }
    fp.update(overrides)
    return fp


class _FakeFingerprint:
    """Stand-in for a FingerprintResult: to_dict() + .findings."""

    def __init__(self, fingerprint=None):
        self._fingerprint = fingerprint if fingerprint is not None else _fingerprint()

    def to_dict(self):
        return self._fingerprint

    @property
    def findings(self):
        return []


async def _register_and_login(client, email: str, company: str) -> dict:
    """Register + login a fresh tenant and return its Authorization header."""
    await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "secret123",
            "name": company,
            "company_name": company,
        },
    )
    resp = await client.post(
        "/auth/login", json={"email": email, "password": "secret123"}
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _patch_discovery(
    monkeypatch,
    subdomains=None,
    fingerprint=None,
):
    """Patch the orchestrator's discovery deps with deterministic fakes.

    Findings are now rule-driven: the fake fingerprint's ``to_dict()`` feeds
    ``finding_rules.evaluate``, so tests control which rules fire by choosing
    the fingerprint dict.
    """
    subdomains = subdomains if subdomains is not None else ["www.example.com"]

    async def _enumerate(domain):
        return subdomains

    def _resolve(hostname, **kwargs):
        return _FakeResolution(ips=["203.0.113.10"])

    async def _fingerprint(hostname, **kwargs):
        return _FakeFingerprint(fingerprint=fingerprint)

    monkeypatch.setattr(orchestrator.crtsh_service, "enumerate_subdomains", _enumerate)
    monkeypatch.setattr(orchestrator.dns_service, "resolve", _resolve)
    monkeypatch.setattr(orchestrator.fp_service, "fingerprint", _fingerprint)


async def _seed_scans(client, headers, monkeypatch):
    """Build a deterministic 5-finding dataset across two assets (PR2).

    Scan 1 (good.example.com, default fingerprint) fires the 3 missing-header
    rules: missing-hsts 5.5, missing-xcto 2.5, missing-csp 5.5.
    Scan 2 (exposed.example.com) is header-healthy but serves port 8443 with
    ``Server: nginx/1.24.0``: nonstandard-port 6.5, server-version-disclosure
    2.5. The 5 findings sort by risk desc: [6.5, 5.5, 5.5, 2.5, 2.5].
    """
    _patch_discovery(monkeypatch)
    await client.post("/asm/scans", json={"domain": "good.example.com"}, headers=headers)

    _patch_discovery(
        monkeypatch,
        fingerprint=_fingerprint(
            strict_transport_security="max-age=31536000",
            x_content_type_options="nosniff",
            content_security_policy="default-src 'self'",
            port=8443,
            server="nginx/1.24.0",
        ),
    )
    await client.post("/asm/scans", json={"domain": "exposed.example.com"}, headers=headers)


def _patch_enumerate_raises(monkeypatch):
    """Make enumeration raise — used to assert the Scan lands on ``error``."""

    async def _enumerate_raises(domain):
        raise RuntimeError("crt.sh exploded unexpectedly")

    async def _resolve(hostname, **kwargs):
        return _FakeResolution(ips=["203.0.113.10"])

    async def _fingerprint(hostname, **kwargs):
        return _FakeFingerprint()

    monkeypatch.setattr(orchestrator.crtsh_service, "enumerate_subdomains", _enumerate_raises)
    monkeypatch.setattr(orchestrator.dns_service, "resolve", _resolve)
    monkeypatch.setattr(orchestrator.fp_service, "fingerprint", _fingerprint)


class TestScanLifecycle:
    """POST /asm/scans persists scan+assets and moves running -> completed."""

    async def test_scan_created_and_completed(self, client, monkeypatch):
        """R-TriggerScan/Valid: discovery persists assets and scan completes."""
        _patch_discovery(monkeypatch)
        headers = await _register_and_login(client, "lifecycle@test.com", "Lifecycle Corp")

        resp = await client.post("/asm/scans", json={"domain": "example.com"}, headers=headers)
        assert resp.status_code == 201
        body = resp.json()

        assert body["scan"]["domain"] == "example.com"
        assert body["scan"]["status"] == "completed"
        assert body["scan"]["started_at"] is not None
        assert body["scan"]["completed_at"] is not None

        # Assets persisted for the discovered live host.
        assert len(body["assets"]) == 1
        asset = body["assets"][0]
        assert asset["subdomain"] == "www.example.com"
        assert asset["ip"] == "203.0.113.10"
        assert asset["service"] == "https"
        assert asset["fingerprint"]["server"] == "nginx"

        # Rule-driven findings are recorded and linked via /asm/results. The
        # default fake fingerprint is https without HSTS/XCTO/CSP, so exactly
        # those three rules fire.
        results = await client.get(f"/asm/results/{body['scan']['id']}", headers=headers)
        assert results.status_code == 200
        findings = results.json()["findings"]
        assert len(findings) == 3
        titles = {f["title"] for f in findings}
        assert "Missing Strict-Transport-Security header" in titles
        assert "Missing X-Content-Type-Options header" in titles
        assert "Missing Content-Security-Policy header" in titles


class TestScanUpsert:
    """Re-scan upserts instead of duplicating (preserve first_seen)."""

    async def test_rescan_no_duplicate_and_preserves_first_seen(self, client, monkeypatch):
        """R-Asset/Upsert via API: second scan of same domain updates, no dup."""
        _patch_discovery(monkeypatch)
        headers = await _register_and_login(client, "upsert@test.com", "Upsert Corp")

        first = await client.post("/asm/scans", json={"domain": "example.com"}, headers=headers)
        first_asset = first.json()["assets"][0]
        first_seen = first_asset["first_seen"]

        second = await client.post("/asm/scans", json={"domain": "example.com"}, headers=headers)
        assert second.status_code == 201
        second_asset = second.json()["assets"][0]

        # Only ONE asset for the subdomain (no duplicate row).
        listed = await client.get("/asm/assets", headers=headers)
        assets = listed.json()["assets"]
        assert len(assets) == 1

        # first_seen preserved, last_seen bumped forward.
        assert second_asset["first_seen"] == first_seen
        assert second_asset["last_seen"] >= first_seen


class TestIsolation:
    """App-level tenant filter: cross-tenant data is 404 / empty."""

    async def test_assets_isolated_between_tenants(self, client, monkeypatch):
        """R-ListAssets/Isolation: tenant A does not see tenant B's assets."""
        _patch_discovery(monkeypatch)
        headers_a = await _register_and_login(client, "a@test.com", "A Corp")
        headers_b = await _register_and_login(client, "b@test.com", "B Corp")

        await client.post("/asm/scans", json={"domain": "a-domain.com"}, headers=headers_a)

        listed_a = await client.get("/asm/assets", headers=headers_a)
        listed_b = await client.get("/asm/assets", headers=headers_b)

        assert len(listed_a.json()["assets"]) == 1
        assert listed_a.json()["assets"][0]["domain"] == "a-domain.com"
        # Tenant B sees none of A's assets.
        assert listed_b.json()["assets"] == []

    async def test_cross_tenant_results_404(self, client, monkeypatch):
        """R-ScanResults/CrossTenant: another tenant's scan_id returns 404."""
        _patch_discovery(monkeypatch)
        headers_a = await _register_and_login(client, "a2@test.com", "A2 Corp")
        headers_b = await _register_and_login(client, "b2@test.com", "B2 Corp")

        scan = await client.post("/asm/scans", json={"domain": "owner.com"}, headers=headers_a)
        scan_id = scan.json()["scan"]["id"]

        results = await client.get(f"/asm/results/{scan_id}", headers=headers_b)
        assert results.status_code == 404
        # No findings leak to the other tenant.
        assert "findings" not in results.json()

    async def test_missing_scan_404(self, client, monkeypatch):
        """A scan id that does not exist returns 404 for the owner too."""
        headers = await _register_and_login(client, "missing@test.com", "Missing Corp")
        resp = await client.get("/asm/results/00000000-0000-0000-0000-000000000000", headers=headers)
        assert resp.status_code == 404


class TestScanError:
    """A discovery failure flips the Scan to ``error`` with completed_at set."""

    async def test_discovery_failure_marks_scan_error(self, client, monkeypatch):
        """R-Scan/Error: unexpected discovery failure -> status=error."""
        _patch_enumerate_raises(monkeypatch)
        headers = await _register_and_login(client, "error@test.com", "Error Corp")

        resp = await client.post("/asm/scans", json={"domain": "bad.com"}, headers=headers)
        # Route still returns the scan; it is marked error, not a 500.
        assert resp.status_code == 201
        body = resp.json()
        assert body["scan"]["status"] == "error"
        assert body["scan"]["completed_at"] is not None
        assert body["assets"] == []


class TestStats:
    """GET /asm/stats returns tenant-scoped counts for the dashboard."""

    async def test_stats_counts_only_own_tenant(self, client, monkeypatch):
        """R-Dashboard: counts reflect data for the requesting tenant only."""
        _patch_discovery(monkeypatch)
        headers_a = await _register_and_login(client, "stats-a@test.com", "Stats A Corp")
        headers_b = await _register_and_login(client, "stats-b@test.com", "Stats B Corp")

        await client.post("/asm/scans", json={"domain": "a-domain.com"}, headers=headers_a)

        # Tenant A: 1 asset, 3 rule-driven findings, 1 scan.
        body_a = (await client.get("/asm/stats", headers=headers_a)).json()
        assert body_a == {"assets": 1, "findings": 3, "scans": 1}

        # Tenant B has no data — counts are zero, nothing leaks from A.
        body_b = (await client.get("/asm/stats", headers=headers_b)).json()
        assert body_b == {"assets": 0, "findings": 0, "scans": 0}

    async def test_stats_requires_auth(self, client):
        """No valid token -> 401."""
        resp = await client.get(
            "/asm/stats", headers={"Authorization": "Bearer not-a-real-token"}
        )
        assert resp.status_code == 401


class TestUnauthenticated:
    """POST /asm/scans requires a valid token (401) and creates no scan."""

    async def test_invalid_token_rejected(self, client, monkeypatch):
        """R-TriggerScan/Unauth: no valid token -> 401, no assets persisted."""
        _patch_discovery(monkeypatch)

        resp = await client.post(
            "/asm/scans",
            json={"domain": "example.com"},
            headers={"Authorization": "Bearer not-a-real-token"},
        )
        assert resp.status_code == 401

        # The authorized owner has no assets, proving no scan ran under the bogus token.
        headers = await _register_and_login(client, "ok@test.com", "Ok Corp")
        listed = await client.get("/asm/assets", headers=headers)
        assert listed.json()["assets"] == []


class TestRiskScoringOrchestration:
    """run_scan evaluates rules, scores findings and recomputes Asset.risk_score."""

    async def test_scan_persists_scored_findings_and_asset_risk(
        self, db_session: AsyncSession, tenant, monkeypatch
    ):
        """R-Rules/Scan: findings persist with score/level/status + asset aggregate."""
        _patch_discovery(monkeypatch)
        scan = await orchestrator.run_scan(
            db_session, tenant_id=tenant.id, domain="example.com"
        )
        assert scan.status == "completed"

        findings = (
            await db_session.execute(select(Finding).where(Finding.scan_id == scan.id))
        ).scalars().all()
        assert len(findings) == 3
        by_type = {f.finding_type: f for f in findings}
        assert set(by_type) == {"missing-hsts", "missing-xcto", "missing-csp"}

        # Scores are deterministic: medium 5 + 0.5 header modifier.
        assert by_type["missing-hsts"].risk_score == 5.5
        assert by_type["missing-hsts"].risk_level == "medium"
        assert by_type["missing-hsts"].status == "open"
        assert by_type["missing-hsts"].remediation  # template attached
        assert by_type["missing-xcto"].risk_score == 2.5
        assert by_type["missing-xcto"].risk_level == "low"

        # Asset aggregate recomputed = max of open findings (5.5).
        asset = (
            await db_session.execute(select(Asset).where(Asset.tenant_id == tenant.id))
        ).scalar_one()
        assert asset.risk_score == 5.5

    async def test_scan_scores_nonstandard_port_and_version_findings(
        self, db_session: AsyncSession, tenant, monkeypatch
    ):
        """Modifiers apply per finding_type during a real scan."""
        _patch_discovery(
            monkeypatch,
            fingerprint=_fingerprint(
                strict_transport_security="max-age=31536000",
                x_content_type_options="nosniff",
                content_security_policy="default-src 'self'",
                port=8443,
                server="nginx/1.24.0",
            ),
        )
        scan = await orchestrator.run_scan(
            db_session, tenant_id=tenant.id, domain="example.com"
        )
        findings = (
            await db_session.execute(select(Finding).where(Finding.scan_id == scan.id))
        ).scalars().all()
        by_type = {f.finding_type: f for f in findings}
        assert set(by_type) == {"nonstandard-port", "server-version-disclosure"}
        # nonstandard-port: medium 5 + 1.5 exposed = 6.5 (max).
        assert by_type["nonstandard-port"].risk_score == 6.5
        # version disclosure: low 2 + 0.5 = 2.5.
        assert by_type["server-version-disclosure"].risk_score == 2.5

        asset = (
            await db_session.execute(select(Asset).where(Asset.tenant_id == tenant.id))
        ).scalar_one()
        assert asset.risk_score == 6.5

    async def test_recompute_asset_risk_max_of_open_findings(
        self, db_session: AsyncSession, tenant
    ):
        """R-Aggregate: risk_score = max of OPEN findings; resolved excluded."""
        asset = Asset(
            tenant_id=tenant.id, domain="example.com", subdomain="www.example.com"
        )
        scan = Scan(tenant_id=tenant.id, domain="example.com", status="completed")
        db_session.add_all([asset, scan])
        await db_session.commit()
        await db_session.refresh(asset)
        await db_session.refresh(scan)

        db_session.add_all(
            [
                Finding(
                    tenant_id=tenant.id, asset_id=asset.id, scan_id=scan.id,
                    severity="high", title="a", finding_type="tls-expired",
                    risk_score=7.5, risk_level="high", status="open",
                ),
                Finding(
                    tenant_id=tenant.id, asset_id=asset.id, scan_id=scan.id,
                    severity="medium", title="b", finding_type="missing-csp",
                    risk_score=3.2, risk_level="medium", status="open",
                ),
                Finding(
                    tenant_id=tenant.id, asset_id=asset.id, scan_id=scan.id,
                    severity="critical", title="c", finding_type="nonstandard-port",
                    risk_score=9.0, risk_level="critical", status="resolved",
                ),
            ]
        )
        await db_session.commit()

        new_value = await orchestrator.recompute_asset_risk(db_session, asset.id)
        assert new_value == 7.5
        await db_session.refresh(asset)
        assert asset.risk_score == 7.5

    async def test_recompute_asset_risk_zero_without_open(
        self, db_session: AsyncSession, tenant
    ):
        """R-Aggregate/Empty: no open findings -> 0.0, not NULL."""
        asset = Asset(
            tenant_id=tenant.id, domain="example.com", subdomain="www.example.com"
        )
        db_session.add(asset)
        await db_session.commit()
        await db_session.refresh(asset)

        new_value = await orchestrator.recompute_asset_risk(db_session, asset.id)
        assert new_value == 0.0
        await db_session.refresh(asset)
        assert asset.risk_score == 0.0


class TestRescanOverwrite:
    """Re-scan overwrites prior findings; aggregate reflects the latest scan."""

    async def test_rescan_overwrites_prior_findings(self, client, monkeypatch):
        """R-Aggregate/Rescan: old findings replaced, no history kept."""
        _patch_discovery(monkeypatch)  # default -> 3 missing-header findings
        headers = await _register_and_login(client, "overwrite@test.com", "Overwrite Corp")

        first = await client.post("/asm/scans", json={"domain": "example.com"}, headers=headers)
        first_scan_id = first.json()["scan"]["id"]
        first_results = await client.get(f"/asm/results/{first_scan_id}", headers=headers)
        assert len(first_results.json()["findings"]) == 3

        # Second scan with a healthy fingerprint except a non-standard port:
        # only nonstandard-port fires -> the old findings are overwritten.
        _patch_discovery(
            monkeypatch,
            fingerprint=_fingerprint(
                strict_transport_security="max-age=31536000",
                x_content_type_options="nosniff",
                content_security_policy="default-src 'self'",
                set_cookie=["session=abc; Secure; HttpOnly"],
                port=8443,
                server="nginx",
            ),
        )
        second = await client.post("/asm/scans", json={"domain": "example.com"}, headers=headers)
        second_scan_id = second.json()["scan"]["id"]
        second_results = await client.get(f"/asm/results/{second_scan_id}", headers=headers)
        findings = second_results.json()["findings"]
        assert len(findings) == 1
        assert findings[0]["title"] == "Exposed service on non-standard port 8443"


# ---------------------------------------------------------------------------
# Phase 3 (PR 2): findings list / risk-summary / asset detail / PATCH / stats
# ---------------------------------------------------------------------------


class TestFindingsList:
    """GET /asm/findings — tenant-scoped, filtered, sorted by risk_score desc."""

    async def test_lists_findings_sorted_by_risk_desc(self, client, monkeypatch):
        """R4/List: findings sorted by risk_score desc with risk fields populated."""
        _patch_discovery(monkeypatch)
        headers = await _register_and_login(client, "findings@test.com", "Findings Corp")
        await _seed_scans(client, headers, monkeypatch)

        resp = await client.get("/asm/findings", headers=headers)
        assert resp.status_code == 200
        body = resp.json()

        assert body["total"] == 5
        assert body["limit"] == 100
        assert body["offset"] == 0
        assert len(body["findings"]) == 5

        scores = [f["risk_score"] for f in body["findings"]]
        assert scores == sorted(scores, reverse=True)
        assert scores[0] == 6.5
        assert body["findings"][0]["finding_type"] == "nonstandard-port"
        assert body["findings"][0]["risk_level"] == "medium"
        assert body["findings"][0]["status"] == "open"
        assert body["findings"][0]["remediation"]
        # Every row carries the scoring contract fields (spec R4).
        assert all(f["risk_score"] is not None for f in body["findings"])
        assert all(
            f["risk_level"] in {"info", "low", "medium", "high", "critical"}
            for f in body["findings"]
        )

    async def test_filters_by_status(self, client, monkeypatch):
        """R4/FilterStatus: ?status=open returns only open findings."""
        _patch_discovery(monkeypatch)
        headers = await _register_and_login(client, "findings-status@test.com", "Findings Status Corp")
        await _seed_scans(client, headers, monkeypatch)

        resp = await client.get("/asm/findings?status=open", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 5
        assert len(body["findings"]) == 5
        assert all(f["status"] == "open" for f in body["findings"])

        # No resolved findings yet -> the filter genuinely returns nothing.
        resolved = await client.get("/asm/findings?status=resolved", headers=headers)
        resolved_body = resolved.json()
        assert resolved_body["total"] == 0
        assert resolved_body["findings"] == []

    async def test_filters_by_severity(self, client, monkeypatch):
        """R4/FilterSeverity: ?severity=medium narrows to medium findings only."""
        _patch_discovery(monkeypatch)
        headers = await _register_and_login(client, "findings-sev@test.com", "Findings Sev Corp")
        await _seed_scans(client, headers, monkeypatch)

        resp = await client.get("/asm/findings?severity=medium", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 3
        assert len(body["findings"]) == 3
        assert all(f["severity"] == "medium" for f in body["findings"])

        low = await client.get("/asm/findings?severity=low", headers=headers)
        assert low.json()["total"] == 2

    async def test_filters_by_asset_id(self, client, monkeypatch):
        """R4/FilterAsset: ?asset_id narrows to one asset's findings."""
        _patch_discovery(monkeypatch)
        headers = await _register_and_login(client, "findings-asset@test.com", "Findings Asset Corp")
        await _seed_scans(client, headers, monkeypatch)

        assets = (await client.get("/asm/assets", headers=headers)).json()["assets"]
        exposed = next(a for a in assets if a["domain"] == "exposed.example.com")

        resp = await client.get(f"/asm/findings?asset_id={exposed['id']}", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        assert len(body["findings"]) == 2
        assert all(f["asset_id"] == exposed["id"] for f in body["findings"])

    async def test_pagination_limit_offset(self, client, monkeypatch):
        """R4/Pagination: limit/offset slice the full set without overlap."""
        _patch_discovery(monkeypatch)
        headers = await _register_and_login(client, "findings-page@test.com", "Findings Page Corp")
        await _seed_scans(client, headers, monkeypatch)

        first = await client.get("/asm/findings?limit=2&offset=0", headers=headers)
        f1 = first.json()
        assert f1["total"] == 5
        assert len(f1["findings"]) == 2

        second = await client.get("/asm/findings?limit=2&offset=2", headers=headers)
        f2 = second.json()
        assert f2["total"] == 5
        assert len(f2["findings"]) == 2

        ids1 = {f["id"] for f in f1["findings"]}
        ids2 = {f["id"] for f in f2["findings"]}
        assert ids1.isdisjoint(ids2)

    async def test_cross_tenant_findings_hidden(self, client, monkeypatch):
        """R4/Isolation: another tenant's list never includes our findings."""
        _patch_discovery(monkeypatch)
        headers_a = await _register_and_login(client, "iso-a@test.com", "Iso A Corp")
        await _seed_scans(client, headers_a, monkeypatch)
        headers_b = await _register_and_login(client, "iso-b@test.com", "Iso B Corp")

        resp = await client.get("/asm/findings", headers=headers_b)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 0
        assert body["findings"] == []

    async def test_requires_auth(self, client):
        """No valid token -> 401."""
        resp = await client.get(
            "/asm/findings", headers={"Authorization": "Bearer not-a-real-token"}
        )
        assert resp.status_code == 401


class TestRiskSummary:
    """GET /asm/risk-summary — tenant-scoped severity/avg/max/open/top overview."""

    async def test_summary_reflects_only_own_tenant(self, client, monkeypatch):
        """R5/Summary: counts, avg/max risk and top findings come from this tenant."""
        _patch_discovery(monkeypatch)
        headers_a = await _register_and_login(client, "summary-a@test.com", "Summary A Corp")
        await _seed_scans(client, headers_a, monkeypatch)
        headers_b = await _register_and_login(client, "summary-b@test.com", "Summary B Corp")

        resp = await client.get("/asm/risk-summary", headers=headers_a)
        assert resp.status_code == 200
        body = resp.json()

        # 5 findings: 3 medium (6.5, 5.5, 5.5) + 2 low (2.5, 2.5).
        assert body["severity_counts"] == {
            "info": 0, "low": 2, "medium": 3, "high": 0, "critical": 0,
        }
        assert body["avg_risk"] == 4.5  # (6.5+5.5+5.5+2.5+2.5)/5
        assert body["max_risk"] == 6.5
        assert body["open_findings"] == 5
        assert len(body["top_findings"]) == 5
        assert body["top_findings"][0]["finding_type"] == "nonstandard-port"
        assert body["top_findings"][0]["risk_score"] == 6.5

        # Tenant B sees zeros — nothing leaks from A.
        resp_b = await client.get("/asm/risk-summary", headers=headers_b)
        body_b = resp_b.json()
        assert body_b["severity_counts"] == {
            "info": 0, "low": 0, "medium": 0, "high": 0, "critical": 0,
        }
        assert body_b["avg_risk"] == 0.0
        assert body_b["max_risk"] == 0.0
        assert body_b["open_findings"] == 0
        assert body_b["top_findings"] == []

    async def test_empty_tenant_returns_zeros(self, client):
        """R5/Empty: a tenant with no findings gets zeroed metrics, 200 not error."""
        headers = await _register_and_login(client, "summary-empty@test.com", "Summary Empty Corp")

        resp = await client.get("/asm/risk-summary", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["severity_counts"] == {
            "info": 0, "low": 0, "medium": 0, "high": 0, "critical": 0,
        }
        assert body["avg_risk"] == 0.0
        assert body["max_risk"] == 0.0
        assert body["open_findings"] == 0
        assert body["top_findings"] == []

    async def test_requires_auth(self, client):
        """No valid token -> 401."""
        resp = await client.get(
            "/asm/risk-summary", headers={"Authorization": "Bearer not-a-real-token"}
        )
        assert resp.status_code == 401


class TestAssetDetail:
    """GET /asm/assets/{id} — asset plus findings, cross-tenant/unknown -> 404."""

    async def test_asset_with_findings(self, client, monkeypatch):
        """R6/Detail: the owner sees the asset and its findings."""
        _patch_discovery(monkeypatch)
        headers = await _register_and_login(client, "asset-detail@test.com", "Asset Detail Corp")
        await _seed_scans(client, headers, monkeypatch)

        assets = (await client.get("/asm/assets", headers=headers)).json()["assets"]
        good = next(a for a in assets if a["domain"] == "good.example.com")

        resp = await client.get(f"/asm/assets/{good['id']}", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["asset"]["id"] == good["id"]
        assert body["asset"]["domain"] == "good.example.com"
        # Aggregate = max of the asset's 3 open findings (5.5, 5.5, 2.5).
        assert body["asset"]["risk_score"] == 5.5
        assert len(body["findings"]) == 3
        scores = [f["risk_score"] for f in body["findings"]]
        assert scores == sorted(scores, reverse=True)
        assert all(f["asset_id"] == good["id"] for f in body["findings"])

    async def test_cross_tenant_asset_404(self, client, monkeypatch):
        """R6/CrossTenant: another tenant's asset id -> 404 with no data leak."""
        _patch_discovery(monkeypatch)
        headers_a = await _register_and_login(client, "asset-iso-a@test.com", "Asset Iso A Corp")
        await _seed_scans(client, headers_a, monkeypatch)
        headers_b = await _register_and_login(client, "asset-iso-b@test.com", "Asset Iso B Corp")

        assets = (await client.get("/asm/assets", headers=headers_a)).json()["assets"]
        target = assets[0]["id"]

        resp = await client.get(f"/asm/assets/{target}", headers=headers_b)
        assert resp.status_code == 404
        assert "asset" not in resp.json()

    async def test_unknown_asset_404(self, client, monkeypatch):
        """R6/Unknown: nonexistent and malformed ids both return 404."""
        _patch_discovery(monkeypatch)
        headers = await _register_and_login(client, "asset-missing@test.com", "Asset Missing Corp")

        missing = await client.get(
            "/asm/assets/00000000-0000-0000-0000-000000000000", headers=headers
        )
        assert missing.status_code == 404

        malformed = await client.get("/asm/assets/not-a-uuid", headers=headers)
        assert malformed.status_code == 404

    async def test_requires_auth(self, client):
        """No valid token -> 401."""
        resp = await client.get(
            "/asm/assets/00000000-0000-0000-0000-000000000000",
            headers={"Authorization": "Bearer not-a-real-token"},
        )
        assert resp.status_code == 401
