"""Device schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.infrastructure.db.models import DevicePlatform, PushProvider
from app.schemas.base import BaseRequest, BaseResponse


class DeviceCreate(BaseRequest):
    """
    Request body for registering a device.

    Notes:
    - `token` must be unique globally.
    - `device_name` is optional but recommended (shown in client UIs).
    """

    platform: DevicePlatform = Field(
        ...,
        description="Device platform: ios, android, or web.",
        examples=["ios"],
    )
    provider: PushProvider = Field(
        default=PushProvider.FCM,
        description="Push provider. Only FCM is supported for now.",
    )
    token: str = Field(
        ...,
        min_length=1,
        description="FCM/APNs token. Must be unique across all devices.",
    )
    device_name: str | None = Field(
        default=None,
        max_length=100,
        description="Human-readable device name (e.g., 'iPhone 15 Pro').",
        examples=["iPhone 15 Pro"],
    )


class DeviceUpdate(BaseRequest):
    """
    Request body for updating a device.

    Only mutable fields are exposed.
    `platform`, `provider`, and `token` are immutable
    (a change would mean a different device).
    """

    device_name: str | None = Field(
        default=None,
        max_length=100,
        description="New human-readable device name.",
    )
    is_active: bool | None = Field(
        default=None,
        description="Set to false to disable this device.",
    )


class DeviceRead(BaseResponse):
    """Response payload for a single Device."""

    id: UUID
    user_id: UUID
    platform: DevicePlatform
    provider: PushProvider
    token: str
    device_name: str | None = None
    is_active: bool
    last_used_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
