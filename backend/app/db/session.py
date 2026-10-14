"""BlackBox Backend — Database session factory."""
from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all ORM models."""


def normalize_database_url(url: str) -> str:
    """Ensure database URL has the proper async driver prefix."""
    url = url.strip()
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://") and not url.startswith("postgresql+"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def _make_engine() -> AsyncEngine:
    settings = get_settings()
    db_url = normalize_database_url(settings.database_url)

    engine_kwargs: dict[str, Any] = {
        "echo": settings.log_level == "DEBUG",
        "pool_pre_ping": True,
    }

    connect_args: dict[str, Any] = {}
    if "sqlite" in db_url:
        connect_args["check_same_thread"] = False
    elif "postgresql" in db_url:
        # Neon PostgreSQL connection pool settings
        engine_kwargs["pool_size"] = settings.db_pool_size
        engine_kwargs["max_overflow"] = settings.db_max_overflow
        engine_kwargs["pool_timeout"] = settings.db_pool_timeout
        engine_kwargs["pool_recycle"] = settings.db_pool_recycle

    engine_kwargs["connect_args"] = connect_args
    return create_async_engine(db_url, **engine_kwargs)


engine = _make_engine()

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
