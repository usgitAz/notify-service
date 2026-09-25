"""User schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field

from app.schemas.base import BaseRequest, BaseResponse


class UserCreate(BaseRequest):
    """
    Request body for creating a User.

    Note:
    - `external_id` is the identifier in the tenant's own system.
    - `email` is optional (a user may only receive push, not email).
    """

    external_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="User identifier in the Tenant's system.",
        examples=["user_123", "ali@example.com"],
    )
    email: EmailStr | None = Field(
        default=None,
        max_length=320,
        description="Optional email address. RFC 5321 max length.",
        examples=["ali@example.com"],
    )


class UserRead(BaseResponse):
    """Response payload for a single User."""

    id: UUID
    tenant_id: UUID
    external_id: str
    email: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
