"""Integration tests for /api/v1/users."""

import pytest
from httpx import AsyncClient

from app.infrastructure.db.models import Tenant


@pytest.mark.integration
class TestCreateUser:
    async def test_happy_path(self, client: AsyncClient, auth_headers):
        response = await client.post(
            "/api/v1/users",
            headers=auth_headers,
            json={"external_id": "ali", "email": "ali@example.com"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["success"] is True
        assert body["data"]["external_id"] == "ali"
        assert body["data"]["email"] == "ali@example.com"

    async def test_duplicate_409(self, client: AsyncClient, auth_headers):
        payload = {"external_id": "dup", "email": "dup@example.com"}
        r1 = await client.post("/api/v1/users", headers=auth_headers, json=payload)
        r2 = await client.post("/api/v1/users", headers=auth_headers, json=payload)
        assert r1.status_code == 201
        assert r2.status_code == 409
        assert r2.json()["error"]["code"] == "USER_ALREADY_EXISTS"

    async def test_missing_api_key_401(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/users",
            json={"external_id": "x"},
        )
        assert response.status_code == 401

    async def test_invalid_api_key_401(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/users",
            headers={"X-API-Key": "sk_live_invalid"},
            json={"external_id": "x"},
        )
        assert response.status_code == 401

    async def test_validation_error_422(self, client: AsyncClient, auth_headers):
        response = await client.post(
            "/api/v1/users",
            headers=auth_headers,
            json={},  # missing external_id
        )
        assert response.status_code == 422


@pytest.mark.integration
class TestGetUser:
    async def test_get_existing(self, client: AsyncClient, auth_headers):
        await client.post(
            "/api/v1/users",
            headers=auth_headers,
            json={"external_id": "get-me", "email": "g@x.com"},
        )
        response = await client.get("/api/v1/users/get-me", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["data"]["external_id"] == "get-me"

    async def test_get_missing_404(self, client: AsyncClient, auth_headers):
        response = await client.get("/api/v1/users/nope", headers=auth_headers)
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "USER_NOT_FOUND"


@pytest.mark.integration
class TestUpdateUser:
    async def test_soft_delete_then_reactivate(self, client: AsyncClient, auth_headers):
        await client.post(
            "/api/v1/users",
            headers=auth_headers,
            json={"external_id": "toggle", "email": "t@x.com"},
        )

        # Soft delete
        r = await client.patch(
            "/api/v1/users/toggle",
            headers=auth_headers,
            json={"is_active": False},
        )
        assert r.status_code == 200
        assert r.json()["data"]["is_active"] is False

        # Should be 404 now (inactive users are filtered)
        r = await client.get("/api/v1/users/toggle", headers=auth_headers)
        assert r.status_code == 404

        # Reactivate via PATCH
        r = await client.patch(
            "/api/v1/users/toggle",
            headers=auth_headers,
            json={"is_active": True},
        )
        assert r.status_code == 200
        assert r.json()["data"]["is_active"] is True


@pytest.mark.integration
class TestCrossTenantIsolation:
    async def test_other_tenant_cannot_see_user(
        self,
        client: AsyncClient,
        auth_headers,
        db_session,
    ):
        from app.core.security import extract_prefix, generate_api_key, hash_api_key

        # Create user in tenant A
        await client.post(
            "/api/v1/users",
            headers=auth_headers,
            json={"external_id": "private", "email": "p@x.com"},
        )

        # Create another tenant
        other_raw = generate_api_key("test")

        other = Tenant(
            name="other",
            api_key_hash=hash_api_key(other_raw),
            api_key_prefix=extract_prefix(other_raw),
        )
        db_session.add(other)
        await db_session.flush()

        # Other tenant cannot see the user
        r = await client.get(
            "/api/v1/users/private",
            headers={"X-API-Key": other_raw},
        )
        assert r.status_code == 404

    async def test_get_invalid_path(self, client: AsyncClient, auth_headers):
        # Empty external_id in URL → 404 or validation
        response = await client.get("/api/v1/users/%20", headers=auth_headers)
        assert response.status_code in (404, 422)
