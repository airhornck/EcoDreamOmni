"""SQLAlchemy 2.0 async database configuration aligned with detailed design §4.

- PostgreSQL 16 + asyncpg
- Alembic migrations (forward-only)
- tenant_id ready for Phase 3 multi-tenancy
"""

import asyncio

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from src.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

Base = declarative_base()


async def get_db() -> AsyncSession:
    """Dependency for FastAPI routes requiring DB access."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_db_optional() -> AsyncSession:
    """Optional DB dependency that yields None on connection failure.
    
    Use this when a route should gracefully degrade when the database
    is unavailable (e.g. Agent-layer routes that also work in-memory).
    """
    try:
        async for session in get_db():
            yield session
    except (GeneratorExit, asyncio.CancelledError):
        raise
    except Exception:
        yield None  # type: ignore[misc]
