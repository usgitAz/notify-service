"""
Notification schemas package.

Public API:
- NotificationRead           → response for any channel
- NotificationListFilters    → query params for listing
- NotificationEmailCreate    → request body for email
"""

from app.schemas.notification.common import (
    NotificationListFilters,
    NotificationRead,
)
from app.schemas.notification.email import NotificationEmailCreate

__all__ = [
    # Common
    "NotificationRead",
    "NotificationListFilters",
    # Channel-specific
    "NotificationEmailCreate",
]
