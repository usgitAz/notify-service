"""Unit tests for EmailClient.

Strategy: patch `aiosmtplib.send` to avoid real network. Test that:
- Mock mode (smtp_enabled=False) → no call.
- Success → no exception.
- Error mapping: PermanentError / TransientError.
- Message building (From, To, Cc, Bcc, Reply-To).
"""

from unittest.mock import AsyncMock, patch

import aiosmtplib
import pytest

from app.core.config import settings
from app.infrastructure.clients.email_client import EmailClient
from app.infrastructure.clients.exceptions import (
    PermanentError,
    TransientError,
)


@pytest.mark.unit
class TestEmailClientMockMode:
    async def test_mock_when_disabled(self, monkeypatch):
        monkeypatch.setattr(settings, "smtp_enabled", False)
        client = EmailClient()
        with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            await client.send(to="x@y.com", subject="s", body="b")
            mock_send.assert_not_called()


@pytest.mark.unit
class TestEmailClientSuccess:
    async def test_send_calls_smtp(self, monkeypatch):
        monkeypatch.setattr(settings, "smtp_enabled", True)
        monkeypatch.setattr(settings, "smtp_from", "sender@x.com")
        monkeypatch.setattr(settings, "smtp_user", "sender@x.com")

        client = EmailClient()
        with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            await client.send(to="x@y.com", subject="Hi", body="Hello")
            mock_send.assert_awaited_once()


@pytest.mark.unit
class TestEmailClientErrorMapping:
    async def test_recipient_refused_permanent(self, monkeypatch):
        monkeypatch.setattr(settings, "smtp_enabled", True)
        client = EmailClient()
        with patch(
            "aiosmtplib.send",
            new_callable=AsyncMock,
            side_effect=aiosmtplib.SMTPRecipientsRefused({}),
        ):
            with pytest.raises(PermanentError) as exc_info:
                await client.send(to="x@y.com", subject="s", body="b")
            assert exc_info.value.reason == "recipient_refused"

    async def test_sender_refused_permanent(self, monkeypatch):
        monkeypatch.setattr(settings, "smtp_enabled", True)
        client = EmailClient()
        with patch(
            "aiosmtplib.send",
            new_callable=AsyncMock,
            side_effect=aiosmtplib.SMTPSenderRefused(550, b"", "sender"),
        ):
            with pytest.raises(PermanentError) as exc_info:
                await client.send(to="x@y.com", subject="s", body="b")
            assert exc_info.value.reason == "sender_refused"

    async def test_auth_error_permanent(self, monkeypatch):
        monkeypatch.setattr(settings, "smtp_enabled", True)
        client = EmailClient()
        with patch(
            "aiosmtplib.send",
            new_callable=AsyncMock,
            side_effect=aiosmtplib.SMTPAuthenticationError(535, b"bad"),
        ):
            with pytest.raises(PermanentError) as exc_info:
                await client.send(to="x@y.com", subject="s", body="b")
            assert exc_info.value.reason == "auth_failed"

    async def test_connect_error_transient(self, monkeypatch):
        monkeypatch.setattr(settings, "smtp_enabled", True)
        client = EmailClient()
        with patch(
            "aiosmtplib.send",
            new_callable=AsyncMock,
            side_effect=aiosmtplib.SMTPConnectError("connection failed"),
        ):
            with pytest.raises(TransientError) as exc_info:
                await client.send(to="x@y.com", subject="s", body="b")
            assert exc_info.value.reason == "smtp_transient"

    async def test_timeout_transient(self, monkeypatch):
        monkeypatch.setattr(settings, "smtp_enabled", True)
        client = EmailClient()
        with (
            patch(
                "aiosmtplib.send",
                new_callable=AsyncMock,
                side_effect=TimeoutError("timed out"),
            ),
            pytest.raises(TransientError),
        ):
            await client.send(to="x@y.com", subject="s", body="b")

    async def test_oserror_transient(self, monkeypatch):
        monkeypatch.setattr(settings, "smtp_enabled", True)
        client = EmailClient()
        with (
            patch(
                "aiosmtplib.send",
                new_callable=AsyncMock,
                side_effect=OSError("network down"),
            ),
            pytest.raises(TransientError),
        ):
            await client.send(to="x@y.com", subject="s", body="b")

    async def test_unknown_smtp_error_transient(self, monkeypatch):
        monkeypatch.setattr(settings, "smtp_enabled", True)
        client = EmailClient()
        with patch(
            "aiosmtplib.send",
            new_callable=AsyncMock,
            side_effect=aiosmtplib.SMTPException("weird"),
        ):
            with pytest.raises(TransientError) as exc_info:
                await client.send(to="x@y.com", subject="s", body="b")
            assert exc_info.value.reason == "smtp_unknown"


@pytest.mark.unit
class TestEmailClientBuildMessage:
    def test_basic_message(self, monkeypatch):
        monkeypatch.setattr(settings, "smtp_from", "from@x.com")
        monkeypatch.setattr(settings, "smtp_from_name", "Service")
        client = EmailClient()
        msg = client._build_message(
            to="to@y.com",
            subject="Hi",
            body="Hello",
            from_email=None,
            reply_to=None,
            cc=None,
            bcc=None,
        )
        assert "Service <from@x.com>" in msg["From"]
        assert msg["To"] == "to@y.com"
        assert msg["Subject"] == "Hi"
        assert msg["Reply-To"] is None

    def test_custom_from(self, monkeypatch):
        monkeypatch.setattr(settings, "smtp_from", "default@x.com")
        monkeypatch.setattr(settings, "smtp_from_name", "Service")
        client = EmailClient()
        msg = client._build_message(
            to="to@y.com",
            subject="Hi",
            body="Hello",
            from_email="custom@x.com",
            reply_to=None,
            cc=None,
            bcc=None,
        )
        assert "custom@x.com" in msg["From"]

    def test_with_cc_bcc_reply_to(self, monkeypatch):
        monkeypatch.setattr(settings, "smtp_from", "f@x.com")
        monkeypatch.setattr(settings, "smtp_from_name", "S")
        client = EmailClient()
        msg = client._build_message(
            to="to@y.com",
            subject="s",
            body="b",
            from_email=None,
            reply_to="reply@x.com",
            cc=["a@x.com", "b@x.com"],
            bcc=["c@x.com"],
        )
        assert msg["Reply-To"] == "reply@x.com"
        assert "a@x.com" in msg["Cc"]
        assert "b@x.com" in msg["Cc"]
        assert "c@x.com" in msg["Bcc"]
