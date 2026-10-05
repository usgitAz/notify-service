"""Unit tests for NotificationService (shared logic)."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundError
from app.infrastructure.db.models import (
    NotificationChannel,
    NotificationStatus,
    User,
)
from app.services.notification_service import NotificationService


@pytest.fixture
def service() -> NotificationService:
    return NotificationService()


# resolve_user
@pytest.mark.unit
class TestNotificationServiceResolveUser:
    async def test_resolves(self, service, fake_tenant, monkeypatch):
        user = User(tenant_id=fake_tenant.id, external_id="ali")
        monkeypatch.setattr(
            service.user_repo, "get_by_external_id", AsyncMock(return_value=user)
        )
        session = AsyncMock()
        result = await service.resolve_user(session, fake_tenant, "ali")
        assert result is user

    async def test_not_found(self, service, fake_tenant, monkeypatch):
        monkeypatch.setattr(
            service.user_repo, "get_by_external_id", AsyncMock(return_value=None)
        )
        session = AsyncMock()
        with pytest.raises(NotFoundError) as exc_info:
            await service.resolve_user(session, fake_tenant, "missing")
        assert exc_info.value.code == "USER_NOT_FOUND"


# persist
@pytest.mark.unit
class TestNotificationServicePersist:
    async def test_persists(self, service, fake_tenant, monkeypatch):
        user = User(tenant_id=fake_tenant.id, external_id="ali")
        user.id = uuid4()

        async def fake_add(session, n):
            n.id = uuid4()
            return n

        monkeypatch.setattr(service.repo, "add", AsyncMock(side_effect=fake_add))
        session = AsyncMock()
        notification = await service.persist(
            session,
            tenant=fake_tenant,
            user=user,
            channel=NotificationChannel.EMAIL,
            title="Hi",
            body="Hello",
            payload={"foo": "bar"},
        )
        assert notification.tenant_id == fake_tenant.id
        assert notification.user_id == user.id
        assert notification.channel == NotificationChannel.EMAIL
        assert notification.title == "Hi"
        assert notification.body == "Hello"
        assert notification.payload == {"foo": "bar"}
        assert notification.status == NotificationStatus.PENDING

    async def test_persists_with_none_title(self, service, fake_tenant, monkeypatch):
        user = User(tenant_id=fake_tenant.id, external_id="ali")
        user.id = uuid4()

        async def fake_add(session, n):
            n.id = uuid4()
            return n

        monkeypatch.setattr(service.repo, "add", AsyncMock(side_effect=fake_add))
        session = AsyncMock()
        notification = await service.persist(
            session,
            tenant=fake_tenant,
            user=user,
            channel=NotificationChannel.PUSH,
            title=None,
            body="Hello",
            payload={},
        )
        assert notification.title is None
        assert notification.channel == NotificationChannel.PUSH


# get_by_id
@pytest.mark.unit
class TestNotificationServiceGetById:
    async def test_returns(self, service, fake_tenant, monkeypatch):
        n = MagicMock()
        n.id = uuid4()
        n.tenant_id = fake_tenant.id
        monkeypatch.setattr(service.repo, "get_with_user", AsyncMock(return_value=n))
        session = AsyncMock()
        result = await service.get_by_id(session, fake_tenant, n.id)
        assert result is n

    async def test_not_found(self, service, fake_tenant, monkeypatch):
        monkeypatch.setattr(service.repo, "get_with_user", AsyncMock(return_value=None))
        session = AsyncMock()
        with pytest.raises(NotFoundError) as exc_info:
            await service.get_by_id(session, fake_tenant, uuid4())
        assert exc_info.value.code == "NOTIFICATION_NOT_FOUND"

    async def test_wrong_tenant(self, service, fake_tenant, monkeypatch):
        """Notification exists but belongs to a different tenant."""
        n = MagicMock()
        n.tenant_id = uuid4()  # different tenant
        monkeypatch.setattr(service.repo, "get_with_user", AsyncMock(return_value=n))
        session = AsyncMock()
        with pytest.raises(NotFoundError):
            await service.get_by_id(session, fake_tenant, uuid4())


# list_by_tenant
@pytest.mark.unit
class TestNotificationServiceList:
    async def test_delegates_to_repo(self, service, fake_tenant, monkeypatch):
        mock = AsyncMock(return_value=([], 0))
        monkeypatch.setattr(service.repo, "list_by_tenant", mock)
        session = AsyncMock()

        items, total = await service.list_by_tenant(session, fake_tenant)

        assert items == []
        assert total == 0
        mock.assert_awaited_once_with(
            session,
            fake_tenant.id,
            status=None,
            channel=None,
            limit=20,
            offset=0,
        )

    async def test_passes_filters(self, service, fake_tenant, monkeypatch):
        mock = AsyncMock(return_value=([], 0))
        monkeypatch.setattr(service.repo, "list_by_tenant", mock)
        session = AsyncMock()

        await service.list_by_tenant(
            session,
            fake_tenant,
            status=NotificationStatus.DELIVERED,
            channel=NotificationChannel.EMAIL,
            limit=5,
            offset=10,
        )

        mock.assert_awaited_once_with(
            session,
            fake_tenant.id,
            status=NotificationStatus.DELIVERED,
            channel=NotificationChannel.EMAIL,
            limit=5,
            offset=10,
        )
