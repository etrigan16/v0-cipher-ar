"""Tests for the Tenant model: creation, slug generation, and constraints."""

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.tenant import Tenant
from app.models.user import User


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


class TestTenantModel:
    """Tenant model: id UUID PK, name, slug unique, created_at."""

    async def test_create_tenant_sets_all_fields(self, db_session: AsyncSession):
        """R1: Tenant created with name generates id, slug, and created_at."""
        tenant = Tenant(name="Acme Corp", slug="acme-corp")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        assert tenant.id is not None
        assert isinstance(tenant.id, uuid.UUID)
        assert tenant.name == "Acme Corp"
        assert tenant.slug == "acme-corp"
        assert tenant.created_at is not None

    async def test_tenant_slug_unique_constraint(self, db_session: AsyncSession):
        """R1: Duplicate slug raises integrity error."""
        tenant_a = Tenant(name="Acme Corp", slug="acme-corp")
        tenant_b = Tenant(name="Acme Corp Also", slug="acme-corp")
        db_session.add(tenant_a)
        await db_session.commit()

        db_session.add(tenant_b)
        with pytest.raises(Exception):
            await db_session.commit()
        await db_session.rollback()

    async def test_query_tenant_by_slug(self, db_session: AsyncSession):
        """R1: Query by slug returns the correct tenant."""
        tenant = Tenant(name="Beta Inc", slug="beta-inc")
        db_session.add(tenant)
        await db_session.commit()

        result = await db_session.execute(
            select(Tenant).where(Tenant.slug == "beta-inc")
        )
        found = result.scalar_one_or_none()
        assert found is not None
        assert found.name == "Beta Inc"

    async def test_tenant_id_is_uuid(self, db_session: AsyncSession):
        """R1: Tenant id is a UUID type."""
        tenant = Tenant(name="Gamma LLC", slug="gamma-llc")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        assert isinstance(tenant.id, uuid.UUID)
        assert len(str(tenant.id)) == 36


class TestUserTenant:
    """User model: tenant_id FK, is_superadmin."""

    async def test_user_created_with_tenant(self, db_session: AsyncSession):
        """R2: New user has tenant_id set and non-null."""
        tenant = Tenant(name="Org", slug="org")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        user = User(
            email="user@org.com",
            name="User",
            hashed_password="hash",
            tenant_id=tenant.id,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.tenant_id == tenant.id
        assert user.is_superadmin is False

    async def test_user_is_superadmin_default_false(self, db_session: AsyncSession):
        """R2: is_superadmin defaults to False."""
        tenant = Tenant(name="Org2", slug="org2")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        user = User(
            email="admin@org2.com",
            name="Admin",
            hashed_password="hash",
            tenant_id=tenant.id,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.is_superadmin is False
