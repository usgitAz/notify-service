"""Integration tests for NotificationRepository JSONB queries."""

import pytest

from app.infrastructure.db.models import (
    Notification,
    NotificationChannel,
    NotificationStatus,
)
from app.repositories.notification_repo import NotificationRepository


@pytest.mark.integration
class TestListEmailByRecipient:
    async def test_empty(self, db_session, tenant):
        repo = NotificationRepository()
        items, total = await repo.list_email_by_recipient(
            db_session, tenant.id, "nobody@x.com"
        )
        assert items == []
        assert total == 0

    async def test_matches_payload_to_email(self, db_session, tenant, user):
        repo = NotificationRepository()
        # Create two notifications to different recipients
        n1 = Notification(
            tenant_id=tenant.id,
            user_id=user.id,
            channel=NotificationChannel.EMAIL,
            title="A",
            body="B",
            status=NotificationStatus.PENDING,
            payload={"to_email": "x@y.com"},
        )
        n2 = Notification(
            tenant_id=tenant.id,
            user_id=user.id,
            channel=NotificationChannel.EMAIL,
            title="C",
            body="D",
            status=NotificationStatus.PENDING,
            payload={"to_email": "other@y.com"},
        )
        db_session.add_all([n1, n2])
        await db_session.flush()

        items, total = await repo.list_email_by_recipient(
            db_session, tenant.id, "x@y.com"
        )
        assert total == 1
        assert items[0].payload["to_email"] == "x@y.com"


@pytest.mark.integration
class TestListEmailWithAttachments:
    async def test_finds_with_attachments(self, db_session, tenant, user):
        repo = NotificationRepository()
        n1 = Notification(
            tenant_id=tenant.id,
            user_id=user.id,
            channel=NotificationChannel.EMAIL,
            title="A",
            body="B",
            status=NotificationStatus.PENDING,
            payload={"attachments": ["x.pdf"]},
        )
        n2 = Notification(
            tenant_id=tenant.id,
            user_id=user.id,
            channel=NotificationChannel.EMAIL,
            title="C",
            body="D",
            status=NotificationStatus.PENDING,
            payload={},
        )
        db_session.add_all([n1, n2])
        await db_session.flush()

        items, total = await repo.list_email_with_attachments(db_session, tenant.id)
        assert total == 1
        assert "attachments" in items[0].payload


@pytest.mark.integration
class TestGetWithUser:
    async def test_found(self, db_session, tenant, user):
        repo = NotificationRepository()
        n = Notification(
            tenant_id=tenant.id,
            user_id=user.id,
            channel=NotificationChannel.EMAIL,
            title="t",
            body="b",
        )
        db_session.add(n)
        await db_session.flush()

        result = await repo.get_with_user(db_session, n.id)
        assert result is not None
        assert result.id == n.id
        assert result.user.id == user.id

    async def test_not_found(self, db_session):
        from uuid import uuid4

        repo = NotificationRepository()
        result = await repo.get_with_user(db_session, uuid4())
        assert result is None


@pytest.mark.integration
class TestListByTenant:
    async def test_empty(self, db_session, tenant):
        repo = NotificationRepository()
        items, total = await repo.list_by_tenant(db_session, tenant.id)
        assert items == []
        assert total == 0

    async def test_returns_all(self, db_session, tenant, user):
        repo = NotificationRepository()
        for i in range(3):
            db_session.add(
                Notification(
                    tenant_id=tenant.id,
                    user_id=user.id,
                    channel=NotificationChannel.EMAIL,
                    title=f"t{i}",
                    body="b",
                    status=NotificationStatus.PENDING,
                )
            )
        await db_session.flush()

        items, total = await repo.list_by_tenant(db_session, tenant.id)
        assert total == 3
        assert len(items) == 3

    async def test_filter_status(self, db_session, tenant, user):
        repo = NotificationRepository()
        db_session.add_all(
            [
                Notification(
                    tenant_id=tenant.id,
                    user_id=user.id,
                    channel=NotificationChannel.EMAIL,
                    title="p",
                    body="b",
                    status=NotificationStatus.PENDING,
                ),
                Notification(
                    tenant_id=tenant.id,
                    user_id=user.id,
                    channel=NotificationChannel.EMAIL,
                    title="d",
                    body="b",
                    status=NotificationStatus.DELIVERED,
                ),
            ]
        )
        await db_session.flush()

        items, total = await repo.list_by_tenant(
            db_session, tenant.id, status=NotificationStatus.DELIVERED
        )
        assert total == 1
        assert items[0].status == NotificationStatus.DELIVERED

    async def test_filter_channel(self, db_session, tenant, user):
        repo = NotificationRepository()
        db_session.add_all(
            [
                Notification(
                    tenant_id=tenant.id,
                    user_id=user.id,
                    channel=NotificationChannel.EMAIL,
                    title="e",
                    body="b",
                ),
                Notification(
                    tenant_id=tenant.id,
                    user_id=user.id,
                    channel=NotificationChannel.PUSH,
                    title="p",
                    body="b",
                ),
            ]
        )
        await db_session.flush()

        items, total = await repo.list_by_tenant(
            db_session, tenant.id, channel=NotificationChannel.PUSH
        )
        assert total == 1
        assert items[0].channel == NotificationChannel.PUSH

    async def test_pagination(self, db_session, tenant, user):
        repo = NotificationRepository()
        for i in range(5):
            db_session.add(
                Notification(
                    tenant_id=tenant.id,
                    user_id=user.id,
                    channel=NotificationChannel.EMAIL,
                    title=f"t{i}",
                    body="b",
                )
            )
        await db_session.flush()

        items, total = await repo.list_by_tenant(
            db_session, tenant.id, limit=2, offset=1
        )
        assert total == 5
        assert len(items) == 2
