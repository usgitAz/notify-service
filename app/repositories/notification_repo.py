"""
Notification repository.

Single repository for ALL channels (unified table).
Channel-specific queries use the `payload` JSONB column.
"""

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
    """Repository for Notification (all channels)."""

    model = Notification

    # Generic reads
    async def get_with_user(
        self,
        session: AsyncSession,
        notification_id: UUID,
    ) -> Notification | None:
        """Fetch a notification with its User eagerly loaded."""
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
        """List notifications for a tenant with optional filters."""
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

    # Channel-specific reads (via JSONB)
    async def list_email_by_recipient(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        recipient_email: str,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Notification], int]:
        """
        List email notifications that went to a specific recipient.

        Matches against `payload->>'to_email'` (denormalized at creation).
        """
        base = select(Notification).where(
            Notification.tenant_id == tenant_id,
            Notification.channel == NotificationChannel.EMAIL,
            Notification.payload["to_email"].astext == recipient_email,
        )

        count_stmt = select(func.count()).select_from(base.subquery())
        total = await session.scalar(count_stmt) or 0

        stmt = base.order_by(Notification.created_at.desc()).limit(limit).offset(offset)
        result = await session.scalars(stmt)
        return list(result), total

    async def list_email_with_attachments(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Notification], int]:
        """List email notifications that have at least one attachment."""
        base = select(Notification).where(
            Notification.tenant_id == tenant_id,
            Notification.channel == NotificationChannel.EMAIL,
            Notification.payload.has_key("attachments"),
        )

        count_stmt = select(func.count()).select_from(base.subquery())
        total = await session.scalar(count_stmt) or 0

        stmt = base.order_by(Notification.created_at.desc()).limit(limit).offset(offset)
        result = await session.scalars(stmt)
        return list(result), total
