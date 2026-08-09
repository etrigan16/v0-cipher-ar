from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.database_url)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


# Tables whose RLS policy isolates by tenant_id (PostgreSQL only). The bool
# marks tables whose NULL-tenant rows (shared seeds, e.g. phishing templates,
# design D9) must remain visible to every tenant: policy becomes
# ``tenant_id = current OR tenant_id IS NULL``.
_TENANT_RLS_TABLES: tuple[tuple[str, bool], ...] = (
    ("assets", False),
    ("scans", False),
    ("findings", False),
    ("templates", True),
    ("campaigns", False),
    ("targets", False),
    ("events", False),
)


def _tenant_isolation_policy(table: str, *, allow_null_tenant: bool = False) -> str:
    """Build the ``tenant_isolation`` CREATE POLICY statement for a table.

    ``allow_null_tenant=True`` additionally exposes rows whose ``tenant_id``
    is NULL (shared seed rows — design D9). Tested via metadata/SQL; the
    runtime requires PostgreSQL (``current_setting``), which SQLite lacks.
    """
    base = "tenant_id = current_setting('app.current_tenant_id')::uuid"
    if allow_null_tenant:
        base = f"{base} OR tenant_id IS NULL"
    return f"CREATE POLICY tenant_isolation ON {table} FOR ALL USING ({base})"


async def get_db():
    async with async_session() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        from app.models.asset import Asset  # noqa: F401 — ensures tables are registered
        from app.models.campaign import Campaign  # noqa: F401
        from app.models.event import Event  # noqa: F401
        from app.models.finding import Finding  # noqa: F401
        from app.models.scan import Scan  # noqa: F401
        from app.models.target import Target  # noqa: F401
        from app.models.template import Template  # noqa: F401
        from app.models.tenant import Tenant  # noqa: F401
        from app.models.user import User  # noqa: F401
        from app.models.waitlist import WaitlistEntry  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)

        # Enable Row-Level Security on tenant-scoped tables (PostgreSQL only)
        # SQLite does not support RLS / SET LOCAL — skip gracefully.
        try:
            await conn.execute(
                text("ALTER TABLE tenants ENABLE ROW LEVEL SECURITY")
            )
            await conn.execute(
                text("ALTER TABLE users ENABLE ROW LEVEL SECURITY")
            )
            await conn.execute(
                text("ALTER TABLE waitlist_entries ENABLE ROW LEVEL SECURITY")
            )

            # Policy: users isolation
            await conn.execute(
                text(
                    """CREATE POLICY tenant_isolation ON users
                    FOR ALL USING (
                        tenant_id = current_setting('app.current_tenant_id')::uuid
                        OR EXISTS (
                            SELECT 1 FROM users
                            WHERE id = current_setting('app.current_user_id')::uuid
                            AND is_superadmin = true
                        )
                    )"""
                )
            )

            # Policy: tenants isolation
            await conn.execute(
                text(
                    """CREATE POLICY tenant_isolation ON tenants
                    FOR ALL USING (
                        id = current_setting('app.current_tenant_id')::uuid
                        OR EXISTS (
                            SELECT 1 FROM users
                            WHERE id = current_setting('app.current_user_id')::uuid
                            AND is_superadmin = true
                        )
                    )"""
                )
            )

            # Policy: waitlist_entries isolation
            await conn.execute(
                text(
                    """CREATE POLICY tenant_isolation ON waitlist_entries
                    FOR ALL USING (
                        tenant_id = current_setting('app.current_tenant_id')::uuid
                        OR EXISTS (
                            SELECT 1 FROM users
                            WHERE id = current_setting('app.current_user_id')::uuid
                            AND is_superadmin = true
                        )
                    )"""
                )
            )

            # RLS for tenant-scoped tables (assets / scans / findings /
            # templates / campaigns / targets / events). Templates additionally
            # expose NULL-tenant seed rows (D9).
            for table, allow_null_tenant in _TENANT_RLS_TABLES:
                await conn.execute(
                    text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
                )
                await conn.execute(
                    text(
                        _tenant_isolation_policy(
                            table, allow_null_tenant=allow_null_tenant
                        )
                    )
                )
        except Exception:
            # Not PostgreSQL (e.g. SQLite in tests) — RLS is not supported
            pass
