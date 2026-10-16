"""User schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, EmailStr, Field

from app.schemas.base import BaseRequest, BaseResponse


class UserCreate(BaseRequest):
    """
    Request body for creating a User.

    Note:
    - `external_id` is the identifier in the tenant's own system.
    - `email` is optional (a user may only receive push, not email).
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "external_id": "user_123",
                "email": "user@example.com",
            }
        }
    )

    external_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="User identifier in the Tenant's system.",
        examples=["user_123", "user@example.com"],
    )
    email: EmailStr | None = Field(
        default=None,
        max_length=320,
        description="Optional email address. RFC 5321 max length.",
        examples=["user@example.com"],
    )


class UserRead(BaseResponse):
    """Response for a single User."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "tenant_id": "c1a2b3d4-e5f6-7890-abcd-ef1234567890",
                "external_id": "user_123",
                "email": "user@example.com",
                "is_active": True,
                "deactivated_at": None,
                "created_at": "2026-10-11T12:00:00Z",
                "updated_at": "2026-10-11T12:00:00Z",
            }
        }
    )

    id: UUID
    tenant_id: UUID
    external_id: str
    email: str | None = None
    is_active: bool
    deactivated_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class UserUpdate(BaseRequest):
    """All fields optional. Omitted fields are left unchanged."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "new@example.com",
                "is_active": True,
            }
        }
    )

    email: EmailStr | None = Field(
        default=None,
        max_length=320,
        description="New email address.",
    )
    is_active: bool | None = Field(
        default=None,
        description="Set to false to deactivate the user (soft delete).",
    )
