from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.db.models import (
    Notification,
    NotificationChannel,
    NotificationStatus,
)
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    """Repository for Notification."""

    model = Notification

    async def get_with_user(
        self,
        session: AsyncSession,
        notification_id: UUID,
    ) -> Notification | None:
        """
        Fetch a notification with its User eagerly loaded.

        Needed for building NotificationRead (user_external_id).
        """
        stmt = (
            select(Notification)
            .options(selectinload(Notification.user))
            .where(Notification.id == notification_id)
        )
        result = await session.scalars(stmt)
        return result.first()

    async def list_by_tenant(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        *,
        status: NotificationStatus | None = None,
        channel: NotificationChannel | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Notification], int]:
        """
        List notifications for a tenant with optional filters.

        Returns (items, total_count) for pagination.
        """
        base = select(Notification).where(Notification.tenant_id == tenant_id)

        if status is not None:
            base = base.where(Notification.status == status)
        if channel is not None:
            base = base.where(Notification.channel == channel)

        # Total (for pagination)
        count_stmt = select(func.count()).select_from(base.subquery())
        total = await session.scalar(count_stmt) or 0

        # Data
        stmt = (
            base.options(selectinload(Notification.user))
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await session.scalars(stmt)
        items = list(result)

        return items, total
