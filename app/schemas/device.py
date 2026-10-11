from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, Field

from app.infrastructure.db.models import DevicePlatform, PushProvider
from app.schemas.base import BaseRequest, BaseResponse


class DeviceCreate(BaseRequest):
    """
    Request body for registering a device.

    Notes:
    - `token` must be unique globally.
    - `device_name` is optional but recommended (shown in client UIs).
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "platform": "ios",
                "provider": "fcm",
                "token": "fcm_token_abc123_def456_ghi789",
                "device_name": "iPhone 15 Pro",
            }
        }
    )

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

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"device_name": "Ali's iPhone"},
                {"is_active": False},
            ]
        }
    )

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
    """Response request for a single Device."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "platform": "ios",
                "provider": "fcm",
                "token": "fcm_token_abc123_def456_ghi789",
                "device_name": "iPhone 15 Pro",
                "is_active": True,
                "last_used_at": "2026-10-11T12:00:00Z",
                "created_at": "2026-10-10T08:00:00Z",
                "updated_at": "2026-10-11T12:00:00Z",
            }
        }
    )

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
