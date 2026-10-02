"""
Notification service — shared logic across all channels.

Responsibilities:
- Resolve user / device.
- Persist a Notification (channel-agnostic).
- Read / list notifications.
- Update delivery state (called by senders).

Channel-specific logic lives in dedicated services:
    notification_email_service.py → create_email()
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.infrastructure.db.models import (
    Notification,
    NotificationChannel,
    NotificationStatus,
    Tenant,
    User,
)
from app.repositories.notification_repo import NotificationRepository
from app.repositories.user_repo import UserRepository


class NotificationService:
    """Shared notification logic."""

    def __init__(self) -> None:
        self.repo = NotificationRepository()
        self.user_repo = UserRepository()

    # Shared helpers (used by channel-specific services)
    async def resolve_user(
        self,
        session: AsyncSession,
        tenant: Tenant,
        external_id: str,
    ) -> User:
        """
        Resolve an active user by external_id.

        Raises NotFoundError if not found.
        """
        user = await self.user_repo.get_by_external_id(session, tenant.id, external_id)
        if user is None:
            raise NotFoundError(
                f"User '{external_id}' not found.",
                code="USER_NOT_FOUND",
            )
        return user

    async def persist(
        self,
        session: AsyncSession,
        *,
        tenant: Tenant,
        user: User,
        channel: NotificationChannel,
        title: str | None,
        body: str,
        payload: dict,
    ) -> Notification:
        """
        Persist a new Notification row in PENDING state.

        Used by channel-specific services.
        """
        notification = Notification(
            tenant_id=tenant.id,
            user_id=user.id,
            channel=channel,
            title=title,
            body=body,
            payload=payload,
            status=NotificationStatus.PENDING,
        )
        await self.repo.add(session, notification)
        return notification

    # Reads
    async def get_by_id(
        self,
        session: AsyncSession,
        tenant: Tenant,
        notification_id: UUID,
    ) -> Notification:
        """Fetch a notification by ID, scoped to the tenant."""
        notification = await self.repo.get_with_user(session, notification_id)
        if notification is None or notification.tenant_id != tenant.id:
            raise NotFoundError(
                f"Notification '{notification_id}' not found.",
                code="NOTIFICATION_NOT_FOUND",
            )
        return notification

    async def list_by_tenant(
        self,
        session: AsyncSession,
        tenant: Tenant,
        *,
        status: NotificationStatus | None = None,
        channel: NotificationChannel | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Notification], int]:
        """List notifications for the tenant."""
        return await self.repo.list_by_tenant(
            session,
            tenant.id,
            status=status,
            channel=channel,
            limit=limit,
            offset=offset,
        )
