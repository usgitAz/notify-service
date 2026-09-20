"""
Device model.

Stores push notification tokens for a User.
Supports multiple devices per user and future providers (APNs, WebPush).

Records are never hard-deleted; only soft-deleted via is_active.
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.infrastructure.db.models.user import User


class DevicePlatform(enum.StrEnum):
    """Supported device platforms."""

    ANDROID = "android"
    IOS = "ios"
    WEB = "web"


class PushProvider(enum.StrEnum):
    """
    Push notification providers.

    Currently only FCM is implemented.
    APNs and WebPush are planned for later phases.
    """

    FCM = "fcm"
    # APNS = "apns"
    # WEBPUSH = "webpush"


class Device(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    """A device registered to receive push notifications."""

    __tablename__ = "devices"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    platform: Mapped[DevicePlatform] = mapped_column(
        SQLEnum(
            DevicePlatform,
            name="device_platform",
            native_enum=False,
            length=20,
        ),
        nullable=False,
    )

    provider: Mapped[PushProvider] = mapped_column(
        SQLEnum(
            PushProvider,
            name="push_provider",
            native_enum=False,
            length=20,
        ),
        nullable=False,
        default=PushProvider.FCM,
        server_default=PushProvider.FCM.value,
    )

    # FCM / APNs token (can be long)
    token: Mapped[str] = mapped_column(Text, nullable=False, unique=True)

    # Last time this device was used (for analytics / cleanup)
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationship
    user: Mapped["User"] = relationship(back_populates="devices")

    __table_args__ = (Index("ix_devices_user_active", "user_id", "is_active"),)

    def __repr__(self) -> str:
        return (
            f"<Device id={self.id} platform={self.platform.value} "
            f"provider={self.provider.value} active={self.is_active}>"
        )
