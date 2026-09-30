from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.infrastructure.db.models import (
    Notification,
    NotificationStatus,
    Tenant,
)
from app.repositories.device_repo import DeviceRepository
from app.repositories.notification_repo import NotificationRepository
from app.repositories.user_repo import UserRepository
from app.schemas.notification import NotificationCreate


class NotificationService:
    """Service for Notification operations."""

    def __init__(self) -> None:
        self.repo = NotificationRepository()
        self.user_repo = UserRepository()
        self.device_repo = DeviceRepository()

    async def create(
        self,
        session: AsyncSession,
        tenant: Tenant,
        payload: NotificationCreate,
    ) -> Notification:
        """
        Create a notification record.

        Steps:
          1. Resolve the user (must be active, belong to tenant).
          2. If device_id is provided, verify it belongs to the user.
          3. Persist a Notification with status=pending.

        NOTE: actual delivery is out of scope here — a later phase
        will pick up pending notifications and dispatch them.
        """
        # 1. Resolve user
        user = await self.user_repo.get_by_external_id(
            session, tenant.id, payload.user_id
        )
        if user is None:
            raise NotFoundError(
                f"User '{payload.user_id}' not found.",
                code="USER_NOT_FOUND",
            )

        # 2. If device_id given, verify ownership
        if payload.device_id is not None:
            device = await self.device_repo.get_active_by_id_and_tenant(
                session, payload.device_id, tenant.id
            )
            if device is None or device.user_id != user.id:
                raise ValidationError(
                    "The device_id does not belong to the given user.",
                    code="DEVICE_NOT_OWNED_BY_USER",
                )

        # 3. Persist
        notification = Notification(
            tenant_id=tenant.id,
            user_id=user.id,
            channel=payload.channel,
            title=payload.title,
            body=payload.body,
            status=NotificationStatus.PENDING,
        )
        await self.repo.add(session, notification)
        return notification

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
        channel=None,
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
