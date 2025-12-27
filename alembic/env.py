"""Alembic migration environment."""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from manik_bot.config import SettingsError, get_database_url
from manik_bot.db import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _get_database_url() -> str:
    """Return database URL from .env or Alembic fallback config."""
    try:
        return get_database_url()
    except SettingsError:
        fallback_url = config.get_main_option("sqlalchemy.url")
        if fallback_url is None:
            raise
        return fallback_url


def run_migrations_offline() -> None:
    """Run migrations without a live database connection."""
    url = _get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with an existing database connection."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations with an async database engine."""
    config.set_main_option("sqlalchemy.url", _get_database_url())
    section = config.get_section(config.config_ini_section)
    if section is None:
        raise SettingsError("Не удалось прочитать конфигурацию Alembic")

    connectable = async_engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations with a live database connection."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
