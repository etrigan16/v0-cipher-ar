from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.database_url)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        from app.models.asset import Asset  # noqa: F401 — ensures tables are registered
        from app.models.finding import Finding  # noqa: F401
        from app.models.scan import Scan  # noqa: F401
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

            # RLS for attack-surface tables (assets / scans / findings)
            for table in ("assets", "scans", "findings"):
                await conn.execute(
                    text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
                )
                await conn.execute(
                    text(
                        f"""CREATE POLICY tenant_isolation ON {table}
                        FOR ALL USING (
                            tenant_id = current_setting('app.current_tenant_id')::uuid
                        )"""
                    )
                )
        except Exception:
            # Not PostgreSQL (e.g. SQLite in tests) — RLS is not supported
            pass
