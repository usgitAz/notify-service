"""Unit tests for app.services.sender."""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.infrastructure.clients.exceptions import (
    PermanentError,
    TransientError,
)
from app.infrastructure.db.models import (
    Notification,
    NotificationChannel,
    NotificationStatus,
)
from app.services import sender


@pytest.mark.unit
class TestSendEmail:
    async def test_happy_path_delivered(self):
        notification = Notification(
            tenant_id=uuid4(),
            user_id=uuid4(),
            channel=NotificationChannel.EMAIL,
            title="Hi",
            body="Hello",
            payload={"to_email": "u@x.com"},
            status=NotificationStatus.PENDING,
        )

        with patch(
            "app.services.sender.email_client.send",
            new_callable=AsyncMock,
        ) as mock_send:
            await sender._send_once(notification)
            mock_send.assert_awaited_once()
            args = mock_send.await_args.kwargs
            assert args["to"] == "u@x.com"
            assert args["subject"] == "Hi"
            assert args["body"] == "Hello"

    async def test_missing_to_email(self):
        notification = Notification(
            tenant_id=uuid4(),
            user_id=uuid4(),
            channel=NotificationChannel.EMAIL,
            title="Hi",
            body="Hello",
            payload={},
        )
        with pytest.raises(PermanentError) as exc_info:
            await sender._send_once(notification)
        assert exc_info.value.reason == "no_to_email"


@pytest.mark.unit
class TestSendOnceUnsupportedChannel:
    async def test_push_not_implemented(self):
        notification = Notification(
            tenant_id=uuid4(),
            user_id=uuid4(),
            channel=NotificationChannel.PUSH,
            title="Hi",
            body="Hello",
            payload={},
        )
        with pytest.raises(PermanentError) as exc_info:
            await sender._send_once(notification)
        assert exc_info.value.reason == "channel_not_implemented"


@pytest.mark.unit
class TestDispatchRetry:
    async def test_permanent_error_marks_failed(self):
        notification = Notification(
            tenant_id=uuid4(),
            user_id=uuid4(),
            channel=NotificationChannel.EMAIL,
            title="Hi",
            body="Hello",
            payload={"to_email": "u@x.com"},
            status=NotificationStatus.PENDING,
        )

        with patch.object(
            sender,
            "_send_once",
            new_callable=AsyncMock,
            side_effect=PermanentError("bad", reason="bad_email"),
        ):
            await sender._dispatch(AsyncMock(), notification)

        assert notification.status == NotificationStatus.FAILED
        assert notification.attempts == 1
        assert "[permanent]" in notification.last_error

    async def test_transient_retries_then_fails(self):
        notification = Notification(
            tenant_id=uuid4(),
            user_id=uuid4(),
            channel=NotificationChannel.EMAIL,
            title="Hi",
            body="Hello",
            payload={"to_email": "u@x.com"},
            status=NotificationStatus.PENDING,
        )

        with (
            patch.object(
                sender,
                "_send_once",
                new_callable=AsyncMock,
                side_effect=TransientError("timeout", reason="smtp"),
            ),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            await sender._dispatch(AsyncMock(), notification)

        assert notification.status == NotificationStatus.FAILED
        assert notification.attempts == sender.MAX_ATTEMPTS

    async def test_transient_then_success(self):
        notification = Notification(
            tenant_id=uuid4(),
            user_id=uuid4(),
            channel=NotificationChannel.EMAIL,
            title="Hi",
            body="Hello",
            payload={"to_email": "u@x.com"},
            status=NotificationStatus.PENDING,
        )

        mock = AsyncMock(
            side_effect=[
                TransientError("boom", reason="smtp"),
                None,  # success on 2nd attempt
            ]
        )
        with (
            patch.object(sender, "_send_once", mock),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            await sender._dispatch(AsyncMock(), notification)

        assert notification.status == NotificationStatus.DELIVERED
        assert notification.attempts == 2
        assert notification.last_error is None


@pytest.mark.unit
class TestSendNotificationEntryPoint:
    async def test_not_found(self, monkeypatch):
        """If notification doesn't exist, log and return."""
        from unittest.mock import AsyncMock, patch

        mock_session = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.get_with_user = AsyncMock(return_value=None)

        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        with (
            patch("app.services.sender.AsyncSessionLocal", return_value=mock_cm),
            patch("app.services.sender.NotificationRepository", return_value=mock_repo),
        ):
            await sender.send_notification(str(uuid4()))
            mock_repo.get_with_user.assert_awaited_once()

    async def test_skips_non_pending(self, monkeypatch):
        """If status != pending, skip."""
        from unittest.mock import AsyncMock, MagicMock, patch

        notification = MagicMock()
        notification.status = NotificationStatus.DELIVERED

        mock_session = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.get_with_user = AsyncMock(return_value=notification)

        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        with (
            patch("app.services.sender.AsyncSessionLocal", return_value=mock_cm),
            patch("app.services.sender.NotificationRepository", return_value=mock_repo),
            patch(
                "app.services.sender._dispatch", new_callable=AsyncMock
            ) as mock_dispatch,
        ):
            await sender.send_notification(str(uuid4()))
            mock_dispatch.assert_not_awaited()

    async def test_dispatch_called(self, monkeypatch):
        """Happy path: dispatch called, session committed."""
        from unittest.mock import AsyncMock, MagicMock, patch

        notification = MagicMock()
        notification.status = NotificationStatus.PENDING

        mock_session = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.get_with_user = AsyncMock(return_value=notification)

        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        with (
            patch("app.services.sender.AsyncSessionLocal", return_value=mock_cm),
            patch("app.services.sender.NotificationRepository", return_value=mock_repo),
            patch(
                "app.services.sender._dispatch", new_callable=AsyncMock
            ) as mock_dispatch,
        ):
            await sender.send_notification(str(uuid4()))
            mock_dispatch.assert_awaited_once()
            mock_session.commit.assert_awaited_once()

    async def test_dispatch_exception_rolls_back(self, monkeypatch):
        """If _dispatch raises, rollback."""
        from unittest.mock import AsyncMock, MagicMock, patch

        notification = MagicMock()
        notification.status = NotificationStatus.PENDING

        mock_session = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.get_with_user = AsyncMock(return_value=notification)

        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        with (
            patch("app.services.sender.AsyncSessionLocal", return_value=mock_cm),
            patch("app.services.sender.NotificationRepository", return_value=mock_repo),
            patch(
                "app.services.sender._dispatch",
                new_callable=AsyncMock,
                side_effect=RuntimeError("boom"),
            ),
        ):
            await sender.send_notification(str(uuid4()))
            mock_session.rollback.assert_awaited_once()
