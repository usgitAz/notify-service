"""Integration tests for health endpoints."""

from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.main import app


@pytest.mark.integration
class TestHealth:
    async def test_liveness(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    async def test_readiness(self, client: AsyncClient):
        response = await client.get("/health/ready")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ready"
        assert body["checks"]["database"] == "ok"

    async def test_readiness_db_down(self, client: AsyncClient):
        """If DB query fails → 503."""

        async def broken_db():
            session = AsyncMock(spec=AsyncSession)
            session.execute.side_effect = OperationalError(
                "connection failed", {}, Exception()
            )
            yield session

        app.dependency_overrides[get_db] = broken_db

        try:
            response = await client.get("/health/ready")
            assert response.status_code == 503
            body = response.json()
            assert body["status"] == "not ready"
            assert body["checks"]["database"].startswith("error:")
        finally:
            app.dependency_overrides.pop(get_db, None)
