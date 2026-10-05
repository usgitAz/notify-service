"""Integration tests for /api/v1/users/{id}/devices and /api/v1/devices/{id}."""

import pytest
from httpx import AsyncClient

from app.infrastructure.db.models import User


@pytest.mark.integration
class TestRegisterDevice:
    async def test_register_happy(
        self,
        client: AsyncClient,
        auth_headers: dict,
        user: User,
    ):
        response = await client.post(
            f"/api/v1/users/{user.external_id}/device/register",
            headers=auth_headers,
            json={
                "platform": "ios",
                "provider": "fcm",
                "token": "tok-1",
                "device_name": "iPhone 15",
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["data"]["token"] == "tok-1"
        assert body["data"]["platform"] == "ios"

    async def test_duplicate_active(
        self,
        client: AsyncClient,
        auth_headers: dict,
        user: User,
    ):
        payload = {"platform": "ios", "token": "same-tok"}
        r1 = await client.post(
            f"/api/v1/users/{user.external_id}/device/register",
            headers=auth_headers,
            json=payload,
        )
        r2 = await client.post(
            f"/api/v1/users/{user.external_id}/device/register",
            headers=auth_headers,
            json=payload,
        )
        assert r1.status_code == 201
        assert r2.status_code == 409
        assert r2.json()["error"]["code"] == "DEVICE_ALREADY_REGISTERED"

    async def test_user_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        response = await client.post(
            "/api/v1/users/nobody/device/register",
            headers=auth_headers,
            json={"platform": "ios", "token": "t"},
        )
        assert response.status_code == 404


@pytest.mark.integration
class TestListDevices:
    async def test_empty(
        self,
        client: AsyncClient,
        auth_headers: dict,
        user: User,
    ):
        response = await client.get(
            f"/api/v1/users/{user.external_id}/devices",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"] == []

    async def test_after_register(
        self,
        client: AsyncClient,
        auth_headers: dict,
        user: User,
    ):
        await client.post(
            f"/api/v1/users/{user.external_id}/device/register",
            headers=auth_headers,
            json={"platform": "ios", "token": "t1"},
        )
        response = await client.get(
            f"/api/v1/users/{user.external_id}/devices",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert len(response.json()["data"]) == 1


@pytest.mark.integration
class TestGetDevice:
    async def test_get_existing(
        self,
        client: AsyncClient,
        auth_headers: dict,
        user: User,
    ):
        r = await client.post(
            f"/api/v1/users/{user.external_id}/device/register",
            headers=auth_headers,
            json={"platform": "ios", "token": "t1"},
        )
        device_id = r.json()["data"]["id"]
        response = await client.get(
            f"/api/v1/devices/{device_id}", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["data"]["id"] == device_id

    async def test_missing(self, client: AsyncClient, auth_headers: dict):
        from uuid import uuid4

        response = await client.get(f"/api/v1/devices/{uuid4()}", headers=auth_headers)
        assert response.status_code == 404


@pytest.mark.integration
class TestUpdateDevice:
    async def test_rename(
        self,
        client: AsyncClient,
        auth_headers: dict,
        user: User,
    ):
        r = await client.post(
            f"/api/v1/users/{user.external_id}/device/register",
            headers=auth_headers,
            json={"platform": "ios", "token": "t1", "device_name": "Old"},
        )
        device_id = r.json()["data"]["id"]
        response = await client.patch(
            f"/api/v1/devices/{device_id}",
            headers=auth_headers,
            json={"device_name": "New"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["device_name"] == "New"

    async def test_deactivate(
        self,
        client: AsyncClient,
        auth_headers: dict,
        user: User,
    ):
        r = await client.post(
            f"/api/v1/users/{user.external_id}/device/register",
            headers=auth_headers,
            json={"platform": "ios", "token": "t1"},
        )
        device_id = r.json()["data"]["id"]
        response = await client.patch(
            f"/api/v1/devices/{device_id}",
            headers=auth_headers,
            json={"is_active": False},
        )
        assert response.status_code == 200
        assert response.json()["data"]["is_active"] is False

        # After deactivation, GET returns 404
        r2 = await client.get(f"/api/v1/devices/{device_id}", headers=auth_headers)
        assert r2.status_code == 404


@pytest.mark.integration
class TestDeviceErrors:
    async def test_invalid_uuid(self, client: AsyncClient, auth_headers: dict):
        response = await client.get("/api/v1/devices/not-a-uuid", headers=auth_headers)
        assert response.status_code == 422

    async def test_list_for_missing_user(self, client: AsyncClient, auth_headers: dict):
        response = await client.get("/api/v1/users/nope/devices", headers=auth_headers)
        assert response.status_code == 404

    async def test_update_deactivated_device(
        self, client: AsyncClient, auth_headers: dict, user: User
    ):
        r = await client.post(
            f"/api/v1/users/{user.external_id}/device/register",
            headers=auth_headers,
            json={"platform": "ios", "token": "tok-x"},
        )
        dev_id = r.json()["data"]["id"]
        # Deactivate
        await client.patch(
            f"/api/v1/devices/{dev_id}",
            headers=auth_headers,
            json={"is_active": False},
        )
        # Now try to update again
        response = await client.patch(
            f"/api/v1/devices/{dev_id}",
            headers=auth_headers,
            json={"device_name": "x"},
        )
        assert response.status_code == 404
