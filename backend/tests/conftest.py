"""Shared pytest fixtures: in-memory SQLite backend with overridden DB dependency.

Design D4: SECRET_KEY is set BEFORE any app import (app.config reads the
environment at import time); the real Postgres engine is never touched
because httpx ASGITransport only sends ``http`` scope messages, so the
FastAPI startup lifespan (``init_db``) never runs.

RLS caveat: SQLite does not support SET LOCAL or current_setting(). RLS-
specific tests must run against PostgreSQL (staging or CI service). The
existing test suite continues with SQLite for model/logic tests; RLS test
fixtures skip in SQLite via pytest.skip(). The ``database.py::init_db``
RLS setup silently catches exceptions on non-PostgreSQL dialects.
"""

import os

# Must happen before `from app.main import app` (config is bound at import).
os.environ["SECRET_KEY"] = "test-secret"
os.environ["RESEND_API_KEY"] = "re_test_key"

import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Session = async_sessionmaker(engine, expire_on_commit=False)


async def override_get_db():
    async with Session() as session:
        yield session


@pytest_asyncio.fixture
async def client():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
    await engine.dispose()
