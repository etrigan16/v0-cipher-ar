"""Tests for the additive risk-scoring migration (004_risk_scoring).

The full alembic chain (001->004) targets PostgreSQL (``gen_random_uuid()``
in 001), so this test executes ONLY the 004 migration module against an
in-memory SQLite database whose schema mirrors the pre-004 (003)
attack-surface tables. It proves the migration artifact itself:

- ``upgrade()`` adds exactly the risk columns (nullable on findings/assets,
  ``status`` NOT NULL default ``open``) and leaves existing rows untouched.
- ``downgrade()`` drops only the added columns; base data remains.

Selective run: ``pytest tests/test_migrations.py``
"""

import importlib.util
from pathlib import Path

import pytest_asyncio
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool

_MIGRATION_FILE = (
    Path(__file__).resolve().parents[1] / "alembic" / "versions" / "004_risk_scoring.py"
)

# Columns 004 adds to each table (the full set per tasks 1.1 / design).
FINDINGS_ADDED = {
    "risk_score",
    "risk_level",
    "finding_type",
    "remediation",
    "context",
    "llm_summary",
    "enriched_at",
    "status",
}
ASSETS_ADDED = {"risk_score"}


def _load_migration():
    """Load the 004 migration module from disk (not a package import)."""
    spec = importlib.util.spec_from_file_location("migration_004_risk_scoring", _MIGRATION_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _pre_004_metadata() -> sa.MetaData:
    """Replica of the 003 (pre-004) attack-surface schema for assets/findings."""
    meta = sa.MetaData()
    sa.Table(
        "assets",
        meta,
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("domain", sa.String(), nullable=False),
        sa.Column("subdomain", sa.String(), nullable=True),
        sa.Column("ip", sa.String(), nullable=True),
        sa.Column("port", sa.Integer(), nullable=True),
        sa.Column("service", sa.String(), nullable=True),
        sa.Column("fingerprint", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("first_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False),
    )
    sa.Table(
        "findings",
        meta,
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("asset_id", sa.Uuid(), nullable=False),
        sa.Column("scan_id", sa.Uuid(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=False),
    )
    return meta


def _apply(sync_conn, fn_name: str) -> None:
    """Run ``upgrade()`` or ``downgrade()`` of 004 on the given connection."""
    ctx = MigrationContext.configure(sync_conn)
    with Operations.context(ctx):  # installs the module-level alembic `op` proxy
        getattr(_load_migration(), fn_name)()


@pytest_asyncio.fixture
async def pre_004_engine():
    """In-memory SQLite engine whose schema matches migration 003."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(_pre_004_metadata().create_all)
    yield engine
    await engine.dispose()


async def test_004_upgrade_adds_columns_and_preserves_rows(pre_004_engine):
    """R-004/Upgrade: new columns are added nullable and legacy rows survive."""
    async with pre_004_engine.begin() as conn:
        await conn.execute(
            sa.text(
                "INSERT INTO findings (id, tenant_id, asset_id, scan_id, severity, title, detail, discovered_at) "
                "VALUES ('00000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001', "
                "'20000000-0000-0000-0000-000000000001', '30000000-0000-0000-0000-000000000001', "
                "'medium', 'Missing HSTS header', 'no HSTS', '2026-08-01 00:00:00')"
            )
        )
        await conn.execute(
            sa.text(
                "INSERT INTO assets (id, tenant_id, domain, status, first_seen, last_seen) "
                "VALUES ('40000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001', "
                "'example.com', 'discovered', '2026-08-01 00:00:00', '2026-08-01 00:00:00')"
            )
        )

        await conn.run_sync(lambda c: _apply(c, "upgrade"))

        def _assert_schema(sync_conn):
            insp = sa.inspect(sync_conn)
            findings_cols = {c["name"]: c for c in insp.get_columns("findings")}
            assets_cols = {c["name"]: c for c in insp.get_columns("assets")}
            assert FINDINGS_ADDED <= set(findings_cols)
            assert ASSETS_ADDED <= set(assets_cols)
            # findings additions are nullable except status (NOT NULL default open)
            assert findings_cols["risk_score"]["nullable"] is True
            assert findings_cols["risk_level"]["nullable"] is True
            assert findings_cols["remediation"]["nullable"] is True
            assert findings_cols["enriched_at"]["nullable"] is True
            assert findings_cols["status"]["nullable"] is False
            # asset aggregate is nullable (legacy rows NULL until next scan)
            assert assets_cols["risk_score"]["nullable"] is True

        await conn.run_sync(_assert_schema)

        # Legacy rows survive; new columns NULL / defaulted, no backfill.
        finding_row = (
            await conn.execute(
                sa.text(
                    "SELECT risk_score, risk_level, status FROM findings "
                    "WHERE id = '00000000-0000-0000-0000-000000000001'"
                )
            )
        ).one()
        assert finding_row.risk_score is None
        assert finding_row.risk_level is None
        assert finding_row.status == "open"

        asset_row = (
            await conn.execute(
                sa.text(
                    "SELECT risk_score, domain FROM assets "
                    "WHERE id = '40000000-0000-0000-0000-000000000001'"
                )
            )
        ).one()
        assert asset_row.risk_score is None
        assert asset_row.domain == "example.com"


async def test_004_downgrade_drops_only_added_columns(pre_004_engine):
    """R-004/Downgrade: only the added columns are dropped; base data remains."""
    async with pre_004_engine.begin() as conn:
        await conn.execute(
            sa.text(
                "INSERT INTO assets (id, tenant_id, domain, status, first_seen, last_seen) "
                "VALUES ('40000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001', "
                "'example.com', 'discovered', '2026-08-01 00:00:00', '2026-08-01 00:00:00')"
            )
        )
        await conn.run_sync(lambda c: _apply(c, "upgrade"))
        await conn.run_sync(lambda c: _apply(c, "downgrade"))

        def _assert_dropped(sync_conn):
            insp = sa.inspect(sync_conn)
            findings_cols = {c["name"] for c in insp.get_columns("findings")}
            assets_cols = {c["name"] for c in insp.get_columns("assets")}
            assert not (FINDINGS_ADDED & findings_cols)
            assert not (ASSETS_ADDED & assets_cols)
            # Base tables and columns survive the downgrade.
            assert {"id", "severity", "title", "detail"} <= findings_cols
            assert {"id", "domain", "subdomain", "status"} <= assets_cols

        await conn.run_sync(_assert_dropped)
