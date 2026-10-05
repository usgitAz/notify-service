"""Unit tests for NotificationEmailService."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundError, ValidationError
from app.infrastructure.db.models import User
from app.schemas.notification import NotificationEmailCreate
from app.services.notification_email_service import NotificationEmailService


@pytest.fixture
def service() -> NotificationEmailService:
    return NotificationEmailService()


@pytest.mark.unit
class TestNotificationEmailServiceCreate:
    async def test_creates_notification(self, service, fake_tenant, monkeypatch):
        user = User(
            tenant_id=fake_tenant.id,
            external_id="ali",
            email="ali@x.com",
        )
        user.id = uuid4()

        monkeypatch.setattr(
            service.shared, "resolve_user", AsyncMock(return_value=user)
        )

        async def fake_persist(session, **kwargs):
            m = MagicMock()
            m.payload = kwargs["payload"]
            m.title = kwargs["title"]
            return m

        monkeypatch.setattr(
            service.shared, "persist", AsyncMock(side_effect=fake_persist)
        )
        session = AsyncMock()
        result = await service.create_email(
            session,
            fake_tenant,
            NotificationEmailCreate(
                user_id="ali",
                subject="Hi",
                body="Hello",
                cc=["a@x.com"],
            ),
        )
        assert result.title == "Hi"
        assert result.payload["to_email"] == "ali@x.com"
        assert result.payload["cc"] == ["a@x.com"]

    async def test_no_email_raises_validation(self, service, fake_tenant, monkeypatch):
        user = User(tenant_id=fake_tenant.id, external_id="ali", email=None)
        monkeypatch.setattr(
            service.shared, "resolve_user", AsyncMock(return_value=user)
        )
        session = AsyncMock()
        with pytest.raises(ValidationError) as exc_info:
            await service.create_email(
                session,
                fake_tenant,
                NotificationEmailCreate(user_id="ali", subject="s", body="b"),
            )
        assert exc_info.value.code == "USER_HAS_NO_EMAIL"

    async def test_user_not_found(self, service, fake_tenant, monkeypatch):
        monkeypatch.setattr(
            service.shared,
            "resolve_user",
            AsyncMock(side_effect=NotFoundError("no user", code="USER_NOT_FOUND")),
        )
        session = AsyncMock()
        with pytest.raises(NotFoundError):
            await service.create_email(
                session,
                fake_tenant,
                NotificationEmailCreate(user_id="nope", subject="s", body="b"),
            )

    async def test_create_email_with_all_optional_fields(
        self, service, fake_tenant, monkeypatch
    ):
        """Cover all payload fields."""
        user = User(
            tenant_id=fake_tenant.id,
            external_id="ali",
            email="ali@x.com",
        )
        user.id = uuid4()
        monkeypatch.setattr(
            service.shared, "resolve_user", AsyncMock(return_value=user)
        )

        async def fake_persist(session, **kwargs):
            m = MagicMock()
            m.payload = kwargs["payload"]
            m.title = kwargs["title"]
            return m

        monkeypatch.setattr(
            service.shared, "persist", AsyncMock(side_effect=fake_persist)
        )
        session = AsyncMock()
        result = await service.create_email(
            session,
            fake_tenant,
            NotificationEmailCreate(
                user_id="ali",
                subject="Hi",
                body="Hello",
                from_email="noreply@x.com",
                reply_to="reply@x.com",
                cc=["a@x.com"],
                bcc=["b@x.com"],
                attachments=["url"],
            ),
        )
        assert result.payload["from_email"] == "noreply@x.com"
        assert result.payload["reply_to"] == "reply@x.com"
        assert result.payload["bcc"] == ["b@x.com"]
        assert result.payload["attachments"] == ["url"]
