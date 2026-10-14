"""Integration tests for GET /api/v1/auth/me."""

import pytest
from httpx import AsyncClient

from app.infrastructure.db.models import Tenant


@pytest.mark.integration
class TestAuthMe:
    async def test_returns_current_tenant(
        self, client: AsyncClient, auth_headers: dict, tenant: Tenant
    ):
        response = await client.get("/api/v1/auth/me", headers=auth_headers)

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        data = body["data"]
        assert data["id"] == str(tenant.id)
        assert data["name"] == tenant.name
        assert data["api_key_prefix"] == tenant.api_key_prefix
        assert data["is_active"] is True
        assert "created_at" in data
        assert "updated_at" in data

    async def test_missing_api_key_returns_401(self, client: AsyncClient):
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"

    async def test_invalid_api_key_returns_401(self, client: AsyncClient):
        response = await client.get(
            "/api/v1/auth/me",
            headers={"X-API-Key": "sk_live_invalid"},
        )
        assert response.status_code == 401

    async def test_does_not_leak_api_key_hash(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.get("/api/v1/auth/me", headers=auth_headers)
        body = response.json()
        # TenantRead deliberately omits api_key_hash.
        assert "api_key_hash" not in body["data"]

    async def test_inactive_tenant_returns_401(
        self, client: AsyncClient, tenant: Tenant, auth_headers: dict, db_session
    ):
        tenant.is_active = False
        await db_session.flush()

        response = await client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 401
