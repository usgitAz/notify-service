"""Integration tests for DeviceRepository."""

import pytest

from app.infrastructure.db.models import Device, DevicePlatform, PushProvider
from app.repositories.device_repo import DeviceRepository


@pytest.mark.integration
class TestGetActiveByIdAndTenant:
    async def test_returns_device(self, db_session, tenant, user):
        repo = DeviceRepository()
        d = Device(
            user_id=user.id,
            platform=DevicePlatform.IOS,
            provider=PushProvider.FCM,
            token="tok-1",
        )
        db_session.add(d)
        await db_session.flush()

        result = await repo.get_active_by_id_and_tenant(db_session, d.id, tenant.id)
        assert result is not None
        assert result.id == d.id

    async def test_wrong_tenant(self, db_session, tenant, user):
        repo = DeviceRepository()
        d = Device(
            user_id=user.id,
            platform=DevicePlatform.IOS,
            provider=PushProvider.FCM,
            token="tok-2",
        )
        db_session.add(d)
        await db_session.flush()

        from uuid import uuid4

        result = await repo.get_active_by_id_and_tenant(db_session, d.id, uuid4())
        assert result is None

    async def test_missing(self, db_session, tenant):
        from uuid import uuid4

        repo = DeviceRepository()
        result = await repo.get_active_by_id_and_tenant(db_session, uuid4(), tenant.id)
        assert result is None


@pytest.mark.integration
class TestGetByToken:
    async def test_found(self, db_session, user):
        repo = DeviceRepository()
        d = Device(
            user_id=user.id,
            platform=DevicePlatform.IOS,
            provider=PushProvider.FCM,
            token="find-me",
        )
        db_session.add(d)
        await db_session.flush()

        result = await repo.get_by_token(db_session, "find-me")
        assert result is not None
        assert result.id == d.id

    async def test_not_found(self, db_session):
        repo = DeviceRepository()
        result = await repo.get_by_token(db_session, "nope")
        assert result is None


@pytest.mark.integration
class TestListByUser:
    async def test_returns_all(self, db_session, user):
        repo = DeviceRepository()
        for i in range(3):
            db_session.add(
                Device(
                    user_id=user.id,
                    platform=DevicePlatform.IOS,
                    provider=PushProvider.FCM,
                    token=f"t{i}",
                )
            )
        await db_session.flush()

        items, total = await repo.list_by_user(db_session, user.id)
        assert total == 3
        assert len(items) == 3

    async def test_filter_active_only(self, db_session, user):
        repo = DeviceRepository()
        active = Device(
            user_id=user.id,
            platform=DevicePlatform.IOS,
            provider=PushProvider.FCM,
            token="active-tok",
        )
        inactive = Device(
            user_id=user.id,
            platform=DevicePlatform.IOS,
            provider=PushProvider.FCM,
            token="inactive-tok",
        )
        inactive.is_active = False
        db_session.add_all([active, inactive])
        await db_session.flush()

        items, total = await repo.list_by_user(db_session, user.id, is_active=True)
        assert total == 1
        assert items[0].token == "active-tok"

    async def test_default_includes_inactive(self, db_session, user):
        repo = DeviceRepository()
        active = Device(
            user_id=user.id,
            platform=DevicePlatform.IOS,
            provider=PushProvider.FCM,
            token="active-tok",
        )
        inactive = Device(
            user_id=user.id,
            platform=DevicePlatform.IOS,
            provider=PushProvider.FCM,
            token="inactive-tok",
        )
        inactive.is_active = False
        db_session.add_all([active, inactive])
        await db_session.flush()

        items, total = await repo.list_by_user(db_session, user.id)  # default None
        assert total == 2
        assert {d.token for d in items} == {"active-tok", "inactive-tok"}

    async def test_pagination(self, db_session, user):
        repo = DeviceRepository()
        for i in range(3):
            db_session.add(
                Device(
                    user_id=user.id,
                    platform=DevicePlatform.IOS,
                    provider=PushProvider.FCM,
                    token=f"p{i}",
                )
            )
        await db_session.flush()

        items, total = await repo.list_by_user(db_session, user.id, limit=2, offset=0)
        assert total == 3
        assert len(items) == 2


@pytest.mark.integration
class TestCountActiveByUser:
    async def test_counts(self, db_session, user):
        repo = DeviceRepository()
        for i in range(3):
            db_session.add(
                Device(
                    user_id=user.id,
                    platform=DevicePlatform.IOS,
                    provider=PushProvider.FCM,
                    token=f"c{i}",
                )
            )
        await db_session.flush()

        count = await repo.count_active_by_user(db_session, user.id)
        assert count == 3

    async def test_zero(self, db_session, user):
        repo = DeviceRepository()
        count = await repo.count_active_by_user(db_session, user.id)
        assert count == 0
