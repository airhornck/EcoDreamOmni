"""Pytest shared fixtures — W14 ORM test support.

Provides async DB session fixture with automatic rollback.
Overrides FastAPI's get_db dependency to use NullPool for test isolation.
Tests gracefully skip when PostgreSQL is unavailable.
"""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

DB_URL = "postgresql+asyncpg://ecodream:ecodream@localhost:5432/ecodream"


# ── DB availability check ──

@pytest.fixture(scope="session")
def db_available() -> bool:
    """Detect if PostgreSQL is reachable."""
    try:
        import asyncpg

        async def _check() -> bool:
            try:
                conn = await asyncpg.connect(DB_URL.replace("+asyncpg", ""))
                await conn.fetch("SELECT 1")
                await conn.close()
                return True
            except Exception:
                return False

        return asyncio.run(_check())
    except Exception:
        return False


@pytest.fixture
def skip_if_no_db(db_available):
    """Use as test parameter to skip when DB is down."""
    if not db_available:
        pytest.skip("PostgreSQL not available", allow_module_level=False)


# ── NullPool get_db override for TestClient isolation ──

async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an isolated DB session per request (NullPool = no connection sharing)."""
    test_engine = create_async_engine(DB_URL, poolclass=NullPool, echo=False)
    TestSession = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with TestSession() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


@pytest.fixture(scope="session", autouse=True)
def setup_db_override(db_available):
    """Auto-override FastAPI get_db when PostgreSQL is available."""
    if db_available:
        from src.main import app
        from src.core.database import get_db, get_db_optional

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_db_optional] = override_get_db


# ── TestClient fixture (context manager for lifespan) ──

@pytest.fixture(scope="session")
def client(db_available):
    """Yield a TestClient with lifespan active for the whole test session."""
    if not db_available:
        pytest.skip("PostgreSQL not available")
    from src.main import app
    with TestClient(app) as c:
        yield c


# ── Direct DB fixture for async ORM tests ──

@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an isolated async DB session per test (for direct ORM service tests)."""
    test_engine = create_async_engine(DB_URL, poolclass=NullPool, echo=False)
    TestSession = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with TestSession() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()
    await test_engine.dispose()


# ── Test helpers ──

async def _async_clear_asset_pool():
    from src.services.asset_pool_function import clear_asset_pool

    test_engine = create_async_engine(DB_URL, poolclass=NullPool, echo=False)
    TestSession = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with TestSession() as db:
        await clear_asset_pool(db)
    await test_engine.dispose()


def sync_clear_asset_pool():
    """Synchronous wrapper for clearing AssetPool (used by legacy sync tests)."""
    asyncio.run(_async_clear_asset_pool())


async def _async_clear_platform_rules():
    from src.services.platform_rule_function import clear_platform_rules

    test_engine = create_async_engine(DB_URL, poolclass=NullPool, echo=False)
    TestSession = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with TestSession() as db:
        await clear_platform_rules(db)
    await test_engine.dispose()


def sync_clear_platform_rules():
    """Synchronous wrapper for clearing PlatformRule (used by legacy sync tests)."""
    asyncio.run(_async_clear_platform_rules())
