"""Database engine and session helpers."""

from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from manik_bot.config import get_database_url


@lru_cache
def get_engine() -> AsyncEngine:
    """Create and cache the async database engine."""
    return create_async_engine(get_database_url(), echo=False)


@lru_cache
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Create and cache the async session factory."""
    return async_sessionmaker(get_engine(), expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Yield an async database session."""
    async with get_session_factory()() as session:
        yield session
