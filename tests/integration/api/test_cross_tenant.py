"""Cross-tenant isolation tests."""

import pytest
from httpx import AsyncClient

from app.core.security import extract_prefix, generate_api_key, hash_api_key
from app.infrastructure.db.models import Tenant, User


@pytest.mark.integration
class TestCrossTenantIsolation:
    async def test_other_tenant_cannot_get_user(
        self,
        client: AsyncClient,
        auth_headers: dict,
        user: User,
        db_session,
    ):
        # Create another tenant
        other_key = generate_api_key("test")
        other = Tenant(
            name="other",
            api_key_hash=hash_api_key(other_key),
            api_key_prefix=extract_prefix(other_key),
        )
        db_session.add(other)
        await db_session.flush()

        response = await client.get(
            f"/api/v1/users/{user.external_id}",
            headers={"X-API-Key": other_key},
        )
        assert response.status_code == 404

    async def test_other_tenant_cannot_get_notification(
        self,
        client: AsyncClient,
        auth_headers: dict,
        user: User,
        db_session,
    ):
        r = await client.post(
            "/api/v1/notifications/email",
            headers=auth_headers,
            json={"user_id": user.external_id, "subject": "s", "body": "b"},
        )
        notif_id = r.json()["data"]["id"]

        other_key = generate_api_key("test")
        other = Tenant(
            name="other2",
            api_key_hash=hash_api_key(other_key),
            api_key_prefix=extract_prefix(other_key),
        )
        db_session.add(other)
        await db_session.flush()

        response = await client.get(
            f"/api/v1/notifications/{notif_id}",
            headers={"X-API-Key": other_key},
        )
        assert response.status_code == 404

    async def test_other_tenant_cannot_get_device(
        self,
        client: AsyncClient,
        auth_headers: dict,
        user: User,
        db_session,
    ):
        r = await client.post(
            f"/api/v1/users/{user.external_id}/device/register",
            headers=auth_headers,
            json={"platform": "ios", "token": "cross-tok"},
        )
        device_id = r.json()["data"]["id"]

        other_key = generate_api_key("test")
        other = Tenant(
            name="other3",
            api_key_hash=hash_api_key(other_key),
            api_key_prefix=extract_prefix(other_key),
        )
        db_session.add(other)
        await db_session.flush()

        response = await client.get(
            f"/api/v1/devices/{device_id}",
            headers={"X-API-Key": other_key},
        )
        assert response.status_code == 404
