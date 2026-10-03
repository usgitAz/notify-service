"""
Email client via SMTP.

Uses aiosmtplib for async SMTP. Designed for Gmail App Passwords,
but works with any STARTTLS-capable SMTP server.
"""

from __future__ import annotations

from email.message import EmailMessage

import aiosmtplib

from app.core.config import settings
from app.core.logging import get_logger
from app.infrastructure.clients.exceptions import (
    PermanentError,
    TransientError,
)

logger = get_logger(__name__)


class EmailClient:
    """Async SMTP client."""

    async def send(
        self,
        *,
        to: str,
        subject: str,
        body: str,
        from_email: str | None = None,
        reply_to: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
    ) -> None:
        """
        Send an email.

        Raises:
            PermanentError: invalid recipient/auth.
            TransientError: transient network/SMTP failure.
        """
        if not settings.smtp_enabled:
            logger.info(
                "email_send_mock",
                to=to,
                subject=subject,
                reason="smtp_disabled",
            )
            return

        message = self._build_message(
            to=to,
            subject=subject,
            body=body,
            from_email=from_email,
            reply_to=reply_to,
            cc=cc,
            bcc=bcc,
        )

        try:
            await aiosmtplib.send(
                message,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_user,
                password=settings.smtp_password,
                start_tls=settings.smtp_use_tls,
                timeout=15,
            )
            logger.info("email_sent", to=to, subject=subject)

        except aiosmtplib.SMTPRecipientsRefused as exc:
            raise PermanentError(
                f"Recipient refused: {exc}",
                reason="recipient_refused",
            ) from exc
        except aiosmtplib.SMTPSenderRefused as exc:
            raise PermanentError(
                f"Sender refused: {exc}",
                reason="sender_refused",
            ) from exc
        except aiosmtplib.SMTPAuthenticationError as exc:
            raise PermanentError(
                f"SMTP auth failed: {exc}",
                reason="auth_failed",
            ) from exc
        except (
            aiosmtplib.SMTPConnectError,
            aiosmtplib.SMTPConnectTimeoutError,
            aiosmtplib.SMTPReadTimeoutError,
            aiosmtplib.SMTPServerDisconnected,
            TimeoutError,
            OSError,
        ) as exc:
            raise TransientError(
                f"SMTP transient error: {exc}",
                reason="smtp_transient",
            ) from exc
        except aiosmtplib.SMTPException as exc:
            raise TransientError(
                f"Unknown SMTP error: {exc}",
                reason="smtp_unknown",
            ) from exc

    def _build_message(
        self,
        *,
        to: str,
        subject: str,
        body: str,
        from_email: str | None,
        reply_to: str | None,
        cc: list[str] | None,
        bcc: list[str] | None,
    ) -> EmailMessage:
        """Build a plain-text EmailMessage."""
        msg = EmailMessage()

        sender = from_email or settings.smtp_from
        msg["From"] = f"{settings.smtp_from_name} <{sender}>"
        msg["To"] = to
        msg["Subject"] = subject

        if reply_to:
            msg["Reply-To"] = reply_to
        if cc:
            msg["Cc"] = ", ".join(cc)
        if bcc:
            msg["Bcc"] = ", ".join(bcc)

        msg.set_content(body)
        return msg


# Singleton instance (stateless, safe to reuse)
email_client = EmailClient()
