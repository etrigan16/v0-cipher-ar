"""Alembic environment configuration for async SQLAlchemy + asyncpg."""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

# Alembic Config object
config = context.config

# Set up loggers
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import all models so Base.metadata is complete
from app.database import Base  # noqa: E402
from app.models.tenant import Tenant  # noqa: E402, F401
from app.models.user import User  # noqa: E402, F401
from app.models.waitlist import WaitlistEntry  # noqa: E402, F401
from app.models.asset import Asset  # noqa: E402, F401
from app.models.scan import Scan  # noqa: E402, F401
from app.models.finding import Finding  # noqa: E402, F401

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Configures the context with just a URL, not an Engine. Calls to
    context.execute() emit the given string to the script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """Run migrations on the given synchronous connection."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations inside a connection."""
    url = config.get_main_option("sqlalchemy.url")
    connectable = create_async_engine(url)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using an async engine."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
