"""
Alembic environment configuration.

This module wires Alembic to our SQLAlchemy metadata and async engine.
It is designed for an async-only application stack (asyncpg + SQLAlchemy 2.0).

Key points:
- We use the async engine from SQLAlchemy 2.0 (not the legacy sync engine).
- The database URL is loaded from application settings (.env), not from alembic.ini.
- All ORM models are imported so that they register on Base.metadata
  (required for `--autogenerate` to detect them).
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Importing the models package also loads all model modules, which is what
# actually registers the tables on Base.metadata.
import app.infrastructure.db.models  # noqa: F401
from alembic import context

# Application imports
# Pull the runtime configuration (DATABASE_URL, etc.) from app settings.
# This keeps credentials out of alembic.ini and in a single source of truth.
from app.core.config import settings

# IMPORTANT:
# Import Base from the package that also imports every model module.
# If we import Base from a lower-level module only, Alembic would not see
# our tables during `--autogenerate` and would generate empty migrations.
from app.infrastructure.db import Base  # noqa: F401

# Alembic config
config = context.config

# Inject the database URL at runtime.
config.set_main_option("sqlalchemy.url", settings.database_url)

# Configure Python logging from alembic.ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The metadata object Alembic uses for autogenerate.
target_metadata = Base.metadata


# Offline mode
def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    In offline mode, Alembic does not connect to the database.
    Instead, it emits SQL to stdout (or a file) based on the URL.

    Useful for:
    - Generating SQL scripts for review.
    - Applying migrations in environments without direct DB access.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Improve autogenerate fidelity in offline mode too.
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# Online mode
def do_run_migrations(connection: Connection) -> None:
    """
    Run migrations using an existing (sync) connection.

    This function is invoked from an async context via `connection.run_sync(...)`.
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # Detect column type changes (e.g., String(100) -> String(255)).
        compare_type=True,
        # Detect server_default changes.
        compare_server_default=True,
        # We use a single schema (public).
        include_schemas=False,
        # `render_as_batch` is only needed for SQLite; disable for PostgreSQL.
        render_as_batch=False,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Create an async engine and run migrations through it.

    We use `NullPool` because:
    - Migration is a short-lived, one-shot operation.
    - There is no benefit to keeping connections open afterwards.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        # Alembic's runtime is synchronous; `run_sync` bridges the two worlds.
        await connection.run_sync(do_run_migrations)

    # Release all DB resources before returning.
    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online mode: spin up an event loop and run migrations."""
    asyncio.run(run_async_migrations())


# Dispatch
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
