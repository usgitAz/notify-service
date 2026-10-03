"""
Notification model.

Represents a single notification send request and its delivery status.
This is a historical record — soft-delete is intentionally not used.

Cross-channel design:
- One table for ALL channels (email, sms, push, ...).
- Shared fields live as columns (status, attempts, user, ...).
- Channel-specific payloads live in `payload` (JSONB):
    - email → {"cc": [...], "bcc": [...], "attachments": [...]}
    - sms   → {"phone_number": "+98912..."}
    - push  → {"image_url": "...", "data": {...}}
Foreign keys use RESTRICT so that related Tenant/User cannot be
hard-deleted while notifications exist (we only soft-delete them).
"""

import enum
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Enum as SQLEnum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.infrastructure.db.models.tenant import Tenant
    from app.infrastructure.db.models.user import User


class NotificationChannel(enum.StrEnum):
    """Supported notification channels."""

    PUSH = "push"
    EMAIL = "email"


class NotificationStatus(enum.StrEnum):
    """Delivery status of a notification."""

    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"


class Notification(UUIDMixin, TimestampMixin, Base):
    """
    A single notification delivery attempt record.

    Note:
    - Does NOT inherit SoftDeleteMixin (historical record).
    - `title` is nullable (SMS does not have a subject).
    - `payload` holds channel-specific fields (JSONB).
    - tenant_id and user_id are required and protected with RESTRICT.
    """

    __tablename__ = "notifications"

    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    channel: Mapped[NotificationChannel] = mapped_column(
        SQLEnum(
            NotificationChannel,
            name="notification_channel",
            native_enum=False,
            length=20,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )

    # Common fields
    # title is optional: email/push have it, SMS does not.
    title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)

    # Channel-specific fields (JSONB)
    # Examples:
    #   email → {"cc": [...], "bcc": [...], "attachments": [...]}
    #   push  → {"image_url": "...", "data": {...}}
    #   sms   → {"phone_number": "+98912..."}
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    # Delivery state
    status: Mapped[NotificationStatus] = mapped_column(
        SQLEnum(
            NotificationStatus,
            name="notification_status",
            native_enum=False,
            length=20,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=NotificationStatus.PENDING,
        server_default=NotificationStatus.PENDING.value,
    )

    attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="notifications")
    user: Mapped["User"] = relationship(back_populates="notifications")

    __table_args__ = (
        Index("ix_notifications_tenant_status", "tenant_id", "status"),
        Index("ix_notifications_tenant_created", "tenant_id", "created_at"),
        Index("ix_notifications_user_created", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<Notification id={self.id} channel={self.channel.value} "
            f"status={self.status.value} attempts={self.attempts}>"
        )
