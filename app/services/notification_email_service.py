"""
Email-specific logic:
- Validate user has an email address.
- Build the email payload (from_email, cc, bcc, attachments, to_email).
- Map `subject` → `Notification.title`.

This service delegates the shared parts (resolve user, persist) to
`NotificationService`.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from app.infrastructure.db.models import (
    Notification,
    NotificationChannel,
    Tenant,
)
from app.schemas.notification import NotificationEmailCreate
from app.services.notification_service import NotificationService


class NotificationEmailService:
    """Email-specific notification logic."""

    def __init__(self) -> None:
        self.shared = NotificationService()

    async def create_email(
        self,
        session: AsyncSession,
        tenant: Tenant,
        request: NotificationEmailCreate,
    ) -> Notification:
        """
        Create an email notification for a user.

        Steps:
          1. Resolve the user.
          2. Ensure the user has an email address.
          3. Build the channel-specific payload.
          4. Persist via the shared service.
        """
        # 1. Resolve user
        user = await self.shared.resolve_user(session, tenant, request.user_id)

        # 2. Require an email address
        if not user.email:
            raise ValidationError(
                f"User '{request.user_id}' has no email address.",
                code="USER_HAS_NO_EMAIL",
            )

        # 3. Build payload (email-specific fields)
        payload: dict = {
            "to_email": user.email,  # denormalized for querying
            "from_email": request.from_email,
            "reply_to": request.reply_to,
            "cc": request.cc or [],
            "bcc": request.bcc or [],
            "attachments": request.attachments or [],
        }

        # 4. Persist via shared service
        return await self.shared.persist(
            session,
            tenant=tenant,
            user=user,
            channel=NotificationChannel.EMAIL,
            title=request.subject,  # subject → title
            body=request.body,
            payload=payload,
        )
