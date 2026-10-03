"""
Notification sender.

Orchestrates delivery of a single notification:
- Loads the notification + user.
- Dispatches via the appropriate channel (only email for now).
- Handles retry logic for TransientErrors.
- Updates status, attempts, last_error.
"""

from __future__ import annotations

import asyncio
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.infrastructure.clients.email_client import email_client
from app.infrastructure.clients.exceptions import (
    PermanentError,
    TransientError,
)
from app.infrastructure.db.models import (
    Notification,
    NotificationChannel,
    NotificationStatus,
)
from app.infrastructure.db.session import AsyncSessionLocal
from app.repositories.notification_repo import NotificationRepository

logger = get_logger(__name__)

# Retry policy
MAX_ATTEMPTS = 3
BACKOFF_BASE_SECONDS = 2  # 2, 4, 8


# Entry point (BackgroundTask)
async def send_notification(notification_id: str) -> None:
    """
    Background task entrypoint.

    Opens its own DB session (not tied to the request).
    """
    async with AsyncSessionLocal() as session:
        repo = NotificationRepository()
        notification = await repo.get_with_user(session, UUID(notification_id))
        if notification is None:
            logger.warning(
                "sender_notification_not_found",
                notification_id=notification_id,
            )
            return

        if notification.status != NotificationStatus.PENDING:
            logger.info(
                "sender_skip_not_pending",
                notification_id=notification_id,
                status=notification.status.value,
            )
            return

        try:
            await _dispatch(session, notification)
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception(
                "sender_unexpected_error",
                notification_id=notification_id,
            )


# Dispatch with retry loop
async def _dispatch(
    session: AsyncSession,
    notification: Notification,
) -> None:
    """Attempt delivery with retries for transient errors."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        notification.attempts = attempt

        try:
            await _send_once(notification)
            notification.status = NotificationStatus.DELIVERED
            notification.last_error = None
            logger.info(
                "notification_delivered",
                notification_id=str(notification.id),
                channel=notification.channel.value,
                attempt=attempt,
            )
            return

        except PermanentError as exc:
            notification.status = NotificationStatus.FAILED
            notification.last_error = f"[permanent] {exc}"
            logger.warning(
                "notification_failed_permanent",
                notification_id=str(notification.id),
                reason=exc.reason,
                error=str(exc),
            )
            return

        except TransientError as exc:
            notification.last_error = f"[transient] {exc}"

            if attempt == MAX_ATTEMPTS:
                notification.status = NotificationStatus.FAILED
                logger.warning(
                    "notification_failed_after_retries",
                    notification_id=str(notification.id),
                    attempts=attempt,
                    reason=exc.reason,
                )
                return

            delay = BACKOFF_BASE_SECONDS**attempt  # 2, 4, 8
            logger.info(
                "notification_retry_scheduled",
                notification_id=str(notification.id),
                attempt=attempt,
                delay_seconds=delay,
            )
            await asyncio.sleep(delay)


# Channel router
async def _send_once(notification: Notification) -> None:
    """Send a single notification via its channel."""
    if notification.channel == NotificationChannel.EMAIL:
        await _send_email(notification)
        return

    # Push is implemented in a later phase.
    raise PermanentError(
        f"Channel '{notification.channel.value}' is not implemented yet.",
        reason="channel_not_implemented",
    )


async def _send_email(notification: Notification) -> None:
    """Send an email notification."""
    payload = notification.payload or {}

    to_email = payload.get("to_email")
    if not to_email:
        raise PermanentError(
            "Email notification has no 'to_email'.",
            reason="no_to_email",
        )

    await email_client.send(
        to=to_email,
        subject=notification.title or "(no subject)",
        body=notification.body,
        from_email=payload.get("from_email"),
        reply_to=payload.get("reply_to"),
        cc=payload.get("cc") or None,
        bcc=payload.get("bcc") or None,
    )
