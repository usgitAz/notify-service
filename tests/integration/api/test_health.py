"""Integration tests for health endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.exc import OperationalError


@pytest.mark.integration
class TestHealth:
    async def test_liveness(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "healthy"

    async def test_readiness_all_ok(self, client: AsyncClient):
        response = await client.get("/health/ready")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ready"
        assert body["checks"]["database"] == "ok"
        assert body["checks"]["redis"] == "ok"

    async def test_readiness_db_down(self, client: AsyncClient, db_session):
        """If DB query fails → 503, database=error, redis still ok."""
        with patch.object(
            db_session,
            "execute",
            new_callable=AsyncMock,
            side_effect=OperationalError("x", {}, Exception()),
        ):
            response = await client.get("/health/ready")
            assert response.status_code == 503
            body = response.json()
            assert body["status"] == "not ready"
            assert body["checks"]["database"].startswith("error:")
            assert body["checks"]["redis"] == "ok"

    async def test_readiness_redis_down(self, client: AsyncClient, redis_client):
        """If Redis PING fails → 503, redis=error, database still ok."""
        with patch.object(
            redis_client,
            "ping",
            new_callable=AsyncMock,
            side_effect=ConnectionError("redis down"),
        ):
            response = await client.get("/health/ready")
            assert response.status_code == 503
            body = response.json()
            assert body["status"] == "not ready"
            assert body["checks"]["database"] == "ok"
            assert body["checks"]["redis"].startswith("error:")

    async def test_readiness_both_down(
        self, client: AsyncClient, db_session, redis_client
    ):
        """Both DB and Redis fail → 503, both show error."""
        with (
            patch.object(
                db_session,
                "execute",
                new_callable=AsyncMock,
                side_effect=OperationalError("x", {}, Exception()),
            ),
            patch.object(
                redis_client,
                "ping",
                new_callable=AsyncMock,
                side_effect=ConnectionError("redis down"),
            ),
        ):
            response = await client.get("/health/ready")
            assert response.status_code == 503
            body = response.json()
            assert body["checks"]["database"].startswith("error:")
            assert body["checks"]["redis"].startswith("error:")

    async def test_readiness_redis_not_configured(
        self, client: AsyncClient, db_session
    ):
        """When redis dependency returns None → redis=RedisNotConfigured."""
        from app.api.deps import get_redis
        from app.main import app as fastapi_app

        fastapi_app.dependency_overrides[get_redis] = lambda: None
        try:
            response = await client.get("/health/ready")
            assert response.status_code == 503
            body = response.json()
            assert body["status"] == "not ready"
            assert body["checks"]["database"] == "ok"
            assert "RedisNotConfigured" in body["checks"]["redis"]
        finally:
            # Restore so other assertions/tests aren't affected
            del fastapi_app.dependency_overrides[get_redis]


@pytest.mark.integration
class TestRequestId:
    async def test_echoed(self, client: AsyncClient):
        response = await client.get("/health", headers={"X-Request-ID": "my-trace"})
        assert response.headers["X-Request-ID"] == "my-trace"

    async def test_generated_when_missing(self, client: AsyncClient):
        response = await client.get("/health")
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 10
