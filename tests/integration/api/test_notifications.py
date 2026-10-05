"""Integration tests for notifications endpoints (common + email)."""

import pytest
from httpx import AsyncClient

from app.infrastructure.db.models import User


@pytest.mark.integration
class TestCreateEmail:
    async def test_happy(
        self,
        client: AsyncClient,
        auth_headers: dict,
        user: User,
    ):
        response = await client.post(
            "/api/v1/notifications/email",
            headers=auth_headers,
            json={
                "user_id": user.external_id,
                "subject": "Hi",
                "body": "Hello",
                "cc": ["a@x.com", "a@x.com"],  # dedupe
            },
        )
        assert response.status_code == 202
        body = response.json()["data"]
        assert body["channel"] == "email"
        assert body["status"] == "pending"
        assert body["payload"]["to_email"] == user.email
        assert body["payload"]["cc"] == ["a@x.com"]

    async def test_user_without_email(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session,
        tenant,
    ):
        u = User(tenant_id=tenant.id, external_id="no-mail", email=None)
        db_session.add(u)
        await db_session.flush()

        response = await client.post(
            "/api/v1/notifications/email",
            headers=auth_headers,
            json={"user_id": "no-mail", "subject": "s", "body": "b"},
        )
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "USER_HAS_NO_EMAIL"

    async def test_unknown_user(self, client: AsyncClient, auth_headers: dict):
        response = await client.post(
            "/api/v1/notifications/email",
            headers=auth_headers,
            json={"user_id": "nope", "subject": "s", "body": "b"},
        )
        assert response.status_code == 404

    async def test_missing_auth(self, client: AsyncClient, user: User):
        response = await client.post(
            "/api/v1/notifications/email",
            json={"user_id": user.external_id, "subject": "s", "body": "b"},
        )
        assert response.status_code == 401


@pytest.mark.integration
class TestIdempotency:
    async def test_same_key_returns_same(
        self,
        client: AsyncClient,
        auth_headers: dict,
        user: User,
    ):
        headers = {**auth_headers, "Idempotency-Key": "abc"}
        payload = {
            "user_id": user.external_id,
            "subject": "Hi",
            "body": "Hello",
        }
        r1 = await client.post(
            "/api/v1/notifications/email", headers=headers, json=payload
        )
        r2 = await client.post(
            "/api/v1/notifications/email", headers=headers, json=payload
        )
        assert r1.status_code == 202
        assert r2.status_code == 202
        assert r1.json()["data"]["id"] == r2.json()["data"]["id"]

    async def test_different_keys_two_notifications(
        self,
        client: AsyncClient,
        auth_headers: dict,
        user: User,
    ):
        payload = {
            "user_id": user.external_id,
            "subject": "Hi",
            "body": "Hello",
        }
        r1 = await client.post(
            "/api/v1/notifications/email",
            headers={**auth_headers, "Idempotency-Key": "k1"},
            json=payload,
        )
        r2 = await client.post(
            "/api/v1/notifications/email",
            headers={**auth_headers, "Idempotency-Key": "k2"},
            json=payload,
        )
        assert r1.json()["data"]["id"] != r2.json()["data"]["id"]

    async def test_no_key_no_cache(
        self,
        client: AsyncClient,
        auth_headers: dict,
        user: User,
    ):
        payload = {
            "user_id": user.external_id,
            "subject": "Hi",
            "body": "Hello",
        }
        r1 = await client.post(
            "/api/v1/notifications/email", headers=auth_headers, json=payload
        )
        r2 = await client.post(
            "/api/v1/notifications/email", headers=auth_headers, json=payload
        )
        assert r1.json()["data"]["id"] != r2.json()["data"]["id"]


@pytest.mark.integration
class TestListAndGet:
    async def test_list_empty(self, client: AsyncClient, auth_headers: dict):
        response = await client.get("/api/v1/notifications/", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["data"] == []

    async def test_list_with_items(
        self,
        client: AsyncClient,
        auth_headers: dict,
        user: User,
    ):
        await client.post(
            "/api/v1/notifications/email",
            headers=auth_headers,
            json={"user_id": user.external_id, "subject": "s", "body": "b"},
        )
        response = await client.get("/api/v1/notifications/", headers=auth_headers)
        assert len(response.json()["data"]) == 1

    async def test_list_filter_channel(
        self,
        client: AsyncClient,
        auth_headers: dict,
        user: User,
    ):
        await client.post(
            "/api/v1/notifications/email",
            headers=auth_headers,
            json={"user_id": user.external_id, "subject": "s", "body": "b"},
        )
        # Filter by push → empty
        response = await client.get(
            "/api/v1/notifications/?channel=push", headers=auth_headers
        )
        assert response.json()["data"] == []

    async def test_get_notification(
        self,
        client: AsyncClient,
        auth_headers: dict,
        user: User,
    ):
        r = await client.post(
            "/api/v1/notifications/email",
            headers=auth_headers,
            json={"user_id": user.external_id, "subject": "s", "body": "b"},
        )
        notif_id = r.json()["data"]["id"]
        response = await client.get(
            f"/api/v1/notifications/{notif_id}", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["data"]["id"] == notif_id

    async def test_get_missing(self, client: AsyncClient, auth_headers: dict):
        from uuid import uuid4

        response = await client.get(
            f"/api/v1/notifications/{uuid4()}", headers=auth_headers
        )
        assert response.status_code == 404

    async def test_get_invalid_uuid(self, client: AsyncClient, auth_headers: dict):
        response = await client.get(
            "/api/v1/notifications/not-a-uuid", headers=auth_headers
        )
        assert response.status_code == 422

    async def test_list_negative_limit(self, client: AsyncClient, auth_headers: dict):
        response = await client.get(
            "/api/v1/notifications/?limit=-1", headers=auth_headers
        )
        assert response.status_code == 422
