"""
Shared test fixtures.

Strategy:
- Unit tests: no DB, mock everything.
- Integration tests: real DB session (per test, rolled back).
- Redis: fakeredis (in-memory) for both.
- Background tasks: mocked to avoid event-loop mismatch.
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

import fakeredis.aioredis
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.security import extract_prefix, generate_api_key, hash_api_key
from app.infrastructure.db.base import Base
from app.infrastructure.db.models import Tenant, User
from app.main import app

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://user:pass@localhost:5433/notif_test",
)


# DB
@pytest_asyncio.fixture
async def test_engine():
    """Function-scoped: create tables fresh per test."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession]:
    """Session rolled back after each test."""
    connection = await test_engine.connect()
    transaction = await connection.begin()
    session = async_sessionmaker(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )()
    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback()
        await connection.close()


# Redis
@pytest_asyncio.fixture
async def redis_client() -> AsyncGenerator[fakeredis.aioredis.FakeRedis]:
    client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield client
    await client.flushall()
    await client.aclose()


# Domain fixtures
@pytest_asyncio.fixture
async def tenant(db_session: AsyncSession) -> Tenant:
    raw_key = generate_api_key("test")
    t = Tenant(
        name="test-tenant",
        api_key_hash=hash_api_key(raw_key),
        api_key_prefix=extract_prefix(raw_key),
    )
    db_session.add(t)
    await db_session.flush()
    await db_session.refresh(t)
    t._raw_api_key = raw_key  # type: ignore[attr-defined]
    return t


@pytest_asyncio.fixture
async def user(db_session: AsyncSession, tenant: Tenant) -> User:
    u = User(
        tenant_id=tenant.id,
        external_id="test-user",
        email="test-user@example.com",
    )
    db_session.add(u)
    await db_session.flush()
    await db_session.refresh(u)
    return u


# HTTP client
@pytest_asyncio.fixture
async def client(
    db_session: AsyncSession,
    redis_client,
) -> AsyncGenerator[AsyncClient]:
    """
    FastAPI test client with:
    - DB dependency overridden.
    - Redis dependency overridden.
    - send_notification (background task) mocked to avoid
      event-loop mismatch and real SMTP calls.
    """
    from app.api.deps import get_db, get_redis

    async def _override_get_db():
        yield db_session

    def _override_get_redis():
        return redis_client

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_redis] = _override_get_redis

    with patch(
        "app.api.v1.endpoints.notifications.email.send_notification",
        new_callable=AsyncMock,
    ) as mock_send:
        transport = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            ac._mock_send = mock_send  # type: ignore[attr-defined]
            yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(tenant: Tenant) -> dict[str, str]:
    return {"X-API-Key": tenant._raw_api_key}  # type: ignore[attr-defined]
