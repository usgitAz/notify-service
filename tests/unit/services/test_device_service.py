"""Unit tests for DeviceService (repos mocked)."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.exceptions import ConflictError, NotFoundError
from app.infrastructure.db.models import DevicePlatform
from app.schemas.device import DeviceCreate, DeviceUpdate
from app.services.device_service import DeviceService


@pytest.fixture
def service() -> DeviceService:
    return DeviceService()


@pytest.mark.unit
class TestDeviceServiceRegister:
    async def test_new_device(self, service, fake_user, monkeypatch):
        monkeypatch.setattr(service.repo, "get_by_token", AsyncMock(return_value=None))
        monkeypatch.setattr(service.repo, "add", AsyncMock(side_effect=lambda s, d: d))
        session = AsyncMock()
        device = await service.register(
            session,
            fake_user,
            DeviceCreate(platform=DevicePlatform.IOS, token="tok-1"),
        )
        assert device.token == "tok-1"
        assert device.user_id == fake_user.id
        assert device.platform == DevicePlatform.IOS

    async def test_token_of_other_user_conflicts(self, service, fake_user, monkeypatch):
        existing = MagicMock()
        existing.user_id = uuid4()  # different user
        monkeypatch.setattr(
            service.repo, "get_by_token", AsyncMock(return_value=existing)
        )
        session = AsyncMock()
        with pytest.raises(ConflictError) as exc_info:
            await service.register(
                session,
                fake_user,
                DeviceCreate(platform=DevicePlatform.IOS, token="tok"),
            )
        assert exc_info.value.code == "DEVICE_TOKEN_TAKEN"

    async def test_duplicate_active_token_conflicts(
        self, service, fake_user, monkeypatch
    ):
        existing = MagicMock()
        existing.user_id = fake_user.id
        existing.is_active = True
        monkeypatch.setattr(
            service.repo, "get_by_token", AsyncMock(return_value=existing)
        )
        session = AsyncMock()
        with pytest.raises(ConflictError) as exc_info:
            await service.register(
                session,
                fake_user,
                DeviceCreate(platform=DevicePlatform.IOS, token="tok"),
            )
        assert exc_info.value.code == "DEVICE_ALREADY_REGISTERED"

    async def test_reactivate_inactive_token(self, service, fake_user, monkeypatch):
        existing = MagicMock()
        existing.user_id = fake_user.id
        existing.is_active = False
        monkeypatch.setattr(
            service.repo, "get_by_token", AsyncMock(return_value=existing)
        )
        session = AsyncMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        result = await service.register(
            session,
            fake_user,
            DeviceCreate(
                platform=DevicePlatform.ANDROID, token="tok", device_name="Pixel"
            ),
        )
        assert result.is_active is True
        assert result.deactivated_at is None
        assert result.device_name == "Pixel"


@pytest.mark.unit
class TestDeviceServiceList:
    async def test_list_calls_repo(self, service, fake_user, monkeypatch):
        expected = [MagicMock(), MagicMock()]
        mock = AsyncMock(return_value=expected)
        monkeypatch.setattr(service.repo, "list_active_by_user", mock)
        session = AsyncMock()
        result = await service.list_by_user(session, fake_user)
        assert result == expected
        mock.assert_awaited_once_with(session, fake_user.id)


@pytest.mark.unit
class TestDeviceServiceGetById:
    async def test_returns_device(self, service, fake_tenant, monkeypatch):
        device = MagicMock()
        monkeypatch.setattr(
            service.repo,
            "get_active_by_id_and_tenant",
            AsyncMock(return_value=device),
        )
        session = AsyncMock()
        result = await service.get_by_id(session, fake_tenant, uuid4())
        assert result is device

    async def test_not_found(self, service, fake_tenant, monkeypatch):
        monkeypatch.setattr(
            service.repo,
            "get_active_by_id_and_tenant",
            AsyncMock(return_value=None),
        )
        session = AsyncMock()
        with pytest.raises(NotFoundError):
            await service.get_by_id(session, fake_tenant, uuid4())


@pytest.mark.unit
class TestDeviceServiceUpdate:
    async def test_update_name(self, service, fake_tenant, monkeypatch):
        device = MagicMock()
        device.device_name = "Old"
        device.is_active = True
        monkeypatch.setattr(
            service.repo,
            "get_active_by_id_and_tenant",
            AsyncMock(return_value=device),
        )
        session = AsyncMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        await service.update(
            session, fake_tenant, uuid4(), DeviceUpdate(device_name="New")
        )
        assert device.device_name == "New"

    async def test_deactivate(self, service, fake_tenant, monkeypatch):
        device = MagicMock()
        device.is_active = True
        device.deactivated_at = None
        monkeypatch.setattr(
            service.repo,
            "get_active_by_id_and_tenant",
            AsyncMock(return_value=device),
        )
        session = AsyncMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        await service.update(
            session, fake_tenant, uuid4(), DeviceUpdate(is_active=False)
        )
        assert device.is_active is False
        assert device.deactivated_at is not None

    async def test_update_not_found(self, service, fake_tenant, monkeypatch):
        monkeypatch.setattr(
            service.repo,
            "get_active_by_id_and_tenant",
            AsyncMock(return_value=None),
        )
        session = AsyncMock()
        with pytest.raises(NotFoundError):
            await service.update(
                session, fake_tenant, uuid4(), DeviceUpdate(device_name="x")
            )
