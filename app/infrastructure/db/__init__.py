"""
Database package public API.

Import models and base classes from here to avoid circular imports.
"""

from app.infrastructure.db.base import (
    Base,
    CreatedAtMixin,
    SoftDeleteMixin,
    TimestampMixin,
    UpdatedAtMixin,
    UUIDMixin,
)
from app.infrastructure.db.models.device import Device, DevicePlatform, PushProvider
from app.infrastructure.db.models.notification import (
    Notification,
    NotificationChannel,
    NotificationStatus,
)
from app.infrastructure.db.models.tenant import Tenant
from app.infrastructure.db.models.user import User

__all__ = [
    # Base & Mixins
    "Base",
    "UUIDMixin",
    "CreatedAtMixin",
    "UpdatedAtMixin",
    "TimestampMixin",
    "SoftDeleteMixin",
    # Models
    "Tenant",
    "User",
    "Device",
    "Notification",
    # Enums
    "DevicePlatform",
    "PushProvider",
    "NotificationChannel",
    "NotificationStatus",
]
