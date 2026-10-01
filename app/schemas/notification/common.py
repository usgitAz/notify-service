"""
Common notification schemas.

Shared across ALL channels (email, sms, push, ...).

Channel-specific request schemas live in their own modules
(e.g., `email.py`, `sms.py`, `push.py`).

`NotificationRead` is the unified response for every channel:
it exposes the common fields plus a free-form `payload` dict
whose contents depend on the channel.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.infrastructure.db.models import (
    NotificationChannel,
    NotificationStatus,
)
from app.schemas.base import BaseRequest, BaseResponse


class NotificationRead(BaseResponse):
    """
    Response payload for a single Notification.

    The `payload` field holds channel-specific data:
        email → {"cc": [...], "bcc": [...], "attachments": [...]}
        push  → {"image_url": "...", "data": {...}}
        sms   → {"phone_number": "+98912..."}
    """

    id: UUID
    tenant_id: UUID
    user_id: UUID
    user_external_id: str | None = Field(
        default=None,
        description="Recipient identifier as known by the tenant.",
    )

    channel: NotificationChannel = Field(
        description="Delivery channel: email, push, (future: sms, ...).",
    )
    title: str | None = Field(
        default=None,
        description="Optional title. Email/push have it; SMS does not.",
    )
    body: str = Field(
        description="Message body (channel-agnostic).",
    )
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Channel-specific data (e.g., cc, attachments, image_url).",
    )

    status: NotificationStatus = Field(
        description=(
            "Delivery status. "
            "`pending` → created but not yet dispatched. "
            "`delivered` → successfully sent. "
            "`failed` → gave up after retries."
        ),
    )
    attempts: int = Field(
        description="Number of delivery attempts so far (0 until first dispatch).",
    )
    last_error: str | None = Field(
        default=None,
        description="Last error message if delivery failed.",
    )

    created_at: datetime
    updated_at: datetime


class NotificationListFilters(BaseRequest):
    """Query parameters for GET /api/v1/notifications."""

    status: NotificationStatus | None = Field(
        default=None,
        description="Filter by delivery status.",
    )
    channel: NotificationChannel | None = Field(
        default=None,
        description="Filter by channel.",
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Page size (1..100).",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Records to skip.",
    )
