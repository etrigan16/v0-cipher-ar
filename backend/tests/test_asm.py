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
