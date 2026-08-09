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

_MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "alembic" / "versions"

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


def _load_migration_module(file_name: str):
    """Load a migration module from disk by file name (not a package import)."""
    spec = importlib.util.spec_from_file_location(
        f"migration_{Path(file_name).stem}", _MIGRATIONS_DIR / file_name
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_migration():
    """Load the 004 migration module from disk (not a package import)."""
    return _load_migration_module("004_risk_scoring.py")


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


# ── 005_phishing ──────────────────────────────────────────────────────────

PHISHING_TABLES = {"templates", "campaigns", "targets", "events"}
SEED_COUNTS = {"bank": 3, "government": 3, "tech": 2}


def _pre_005_metadata() -> sa.MetaData:
    """Replica of the 004 (pre-005) schema: existing tables, no phishing tables."""
    meta = sa.MetaData()
    sa.Table(
        "tenants",
        meta,
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    return meta


def _apply_005(sync_conn, fn_name: str) -> None:
    """Run ``upgrade()`` or ``downgrade()`` of 005 on the given connection."""
    ctx = MigrationContext.configure(sync_conn)
    with Operations.context(ctx):  # installs the module-level alembic `op` proxy
        getattr(_load_migration_module("005_phishing.py"), fn_name)()


@pytest_asyncio.fixture
async def pre_005_engine():
    """In-memory SQLite engine whose schema matches migration 004."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(_pre_005_metadata().create_all)
    yield engine
    await engine.dispose()


async def test_005_upgrade_creates_tables_constraints_and_seeds(pre_005_engine):
    """R1/R3: upgrade creates the 4 tables, target uniqueness, and 8 seeds."""
    async with pre_005_engine.begin() as conn:
        await conn.run_sync(lambda c: _apply_005(c, "upgrade"))

        def _assert_schema(sync_conn):
            insp = sa.inspect(sync_conn)
            assert PHISHING_TABLES <= set(insp.get_table_names())
            target_cols = {c["name"] for c in insp.get_columns("targets")}
            assert {
                "id", "tenant_id", "campaign_id", "email", "name",
                "status", "tracking_token", "created_at",
            } <= target_cols
            event_cols = {c["name"] for c in insp.get_columns("events")}
            assert {"id", "tenant_id", "campaign_id", "target_id", "type", "metadata", "occurred_at"} <= event_cols
            # unique tracking_token index + (tenant_id, campaign_id, email) constraint
            target_indexes = {i["name"]: i for i in insp.get_indexes("targets")}
            assert "ix_targets_tracking_token" in target_indexes
            # SQLite inspector reports `unique` as 1, Postgres as True — truthy covers both.
            assert target_indexes["ix_targets_tracking_token"]["unique"]
            assert "uq_targets_tenant_campaign_email" in {
                c["name"] for c in insp.get_unique_constraints("targets")
            }
            # composite events index for results aggregation
            assert "ix_events_campaign_type" in {i["name"] for i in insp.get_indexes("events")}

        await conn.run_sync(_assert_schema)

        def _assert_seeds(sync_conn):
            rows = sync_conn.execute(
                sa.text("SELECT category, subject, html_body, tenant_id FROM templates")
            ).all()
            assert len(rows) == 8
            assert all(r.tenant_id is None for r in rows)  # NULL tenant = shared seed (D9)
            counts: dict[str, int] = {}
            for r in rows:
                counts[r.category] = counts.get(r.category, 0) + 1
                blob = f"{r.subject} {r.html_body}"
                assert "{{nombre}}" in blob
                assert "{{empresa}}" in blob
                assert "{{link}}" in blob
            assert counts == SEED_COUNTS

        await conn.run_sync(_assert_seeds)


async def test_005_downgrade_drops_only_phishing_tables(pre_005_engine):
    """Rollback: downgrade drops the 4 tables; the pre-existing tenants table stays."""
    async with pre_005_engine.begin() as conn:
        await conn.run_sync(lambda c: _apply_005(c, "upgrade"))
        await conn.run_sync(lambda c: _apply_005(c, "downgrade"))

        def _assert(sync_conn):
            insp = sa.inspect(sync_conn)
            tables = set(insp.get_table_names())
            assert not (PHISHING_TABLES & tables)
            assert "tenants" in tables

        await conn.run_sync(_assert)
