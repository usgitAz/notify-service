"""Integration tests for authentication (get_current_tenant)."""

import pytest
from httpx import AsyncClient

from app.core.security import extract_prefix, generate_api_key, hash_api_key
from app.infrastructure.db.models import Tenant


@pytest.mark.integration
class TestAuthEdgeCases:
    async def test_missing_header(self, client: AsyncClient):
        response = await client.get("/api/v1/users/nobody")
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"

    async def test_empty_header(self, client: AsyncClient):
        response = await client.get(
            "/api/v1/users/nobody",
            headers={"X-API-Key": ""},
        )
        assert response.status_code == 401

    async def test_wrong_prefix_format(self, client: AsyncClient):
        response = await client.get(
            "/api/v1/users/nobody",
            headers={"X-API-Key": "not-a-valid-key"},
        )
        assert response.status_code == 401

    async def test_valid_prefix_wrong_hash(self, client: AsyncClient, tenant):
        # Use the same prefix but wrong random part
        prefix = tenant.api_key_prefix
        fake_key = f"{prefix}_wrong_random_part_here"
        # Ensure format looks valid (sk_test_...)
        if not fake_key.startswith("sk_"):
            fake_key = f"sk_test_{fake_key}"
        response = await client.get(
            "/api/v1/users/nobody",
            headers={"X-API-Key": fake_key},
        )
        assert response.status_code == 401

    async def test_inactive_tenant_rejected(self, client: AsyncClient, db_session):
        raw = generate_api_key("test")
        t = Tenant(
            name="inactive",
            api_key_hash=hash_api_key(raw),
            api_key_prefix=extract_prefix(raw),
        )
        t.is_active = False
        db_session.add(t)
        await db_session.flush()

        response = await client.get(
            "/api/v1/users/nobody",
            headers={"X-API-Key": raw},
        )
        assert response.status_code == 401
