"""
Notification schemas.

Targeting modes (mutually exclusive):
- user_id only         → all active devices of the user.
- user_id + platform   → all active devices of that platform.
- user_id + device_id  → one specific device.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field, model_validator

from app.infrastructure.db.models import (
    DevicePlatform,
    NotificationChannel,
    NotificationStatus,
)
from app.schemas.base import BaseRequest, BaseResponse


class NotificationCreate(BaseRequest):
    """
    Request body for POST /api/v1/notifications.

    Targeting rules:
    -  user_id  alone          → all active devices of the user.
    -  user_id  +  platform    → all active devices of that platform.
    -  user_id  +  device_id   → that specific device.

     platform  and  device_id  are mutually exclusive.
    """

    user_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Recipient identifier in the Tenant's system.",
        examples=["ali@example.com"],
    )

    channel: NotificationChannel = Field(
        ...,
        description="Delivery channel: push or email.",
    )

    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        examples=["Welcome!"],
    )
    body: str = Field(
        ...,
        min_length=1,
        examples=["Thanks for signing up."],
    )

    # Targeting (optional, mutually exclusive)
    platform: DevicePlatform | None = Field(
        default=None,
        description=(
            "Target all active devices of this platform (ios/android/web). "
            "Only for channel=push."
        ),
        examples=["ios"],
    )
    device_id: UUID | None = Field(
        default=None,
        description=(
            "Target a specific device by ID. "
            "Discover IDs via GET /users/{user_id}/devices."
        ),
    )

    # Cross-field validation
    @model_validator(mode="after")
    def _validate_targeting(self) -> NotificationCreate:
        if self.device_id is not None and self.platform is not None:
            raise ValueError("device_id and platform cannot be combined.")
        return self


class NotificationRead(BaseResponse):
    """Response payload for a single Notification."""

    id: UUID
    tenant_id: UUID
    user_id: UUID
    user_external_id: str | None = Field(
        default=None,
        description="Recipient identifier as known by the tenant.",
    )

    channel: NotificationChannel
    title: str
    body: str

    status: NotificationStatus
    attempts: int
    last_error: str | None = None

    created_at: datetime
    updated_at: datetime


# List filters
class NotificationListFilters(BaseRequest):
    """Query parameters for GET /api/v1/notifications."""

    status: NotificationStatus | None = Field(default=None)
    channel: NotificationChannel | None = Field(default=None)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
