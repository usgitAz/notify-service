"""Tenant schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseRequest, BaseResponse


class TenantCreate(BaseRequest):
    """Input for creating a Tenant (CLI or future route)."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable tenant name.",
        examples=["Shop X"],
    )


class TenantRead(BaseResponse):
    """Response payload for a single Tenant.

    Note: `api_key_hash` is intentionally omitted.
    """

    id: UUID
    name: str
    api_key_prefix: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TenantWithApiKey(BaseResponse):
    """
    Returned ONLY at creation time.

    Contains the raw API key. It is never returned again —
    if lost, the tenant must rotate (or be recreated).
    """

    tenant: TenantRead
    api_key: str = Field(
        ...,
        description="Raw API key. Store securely — shown only once.",
    )
