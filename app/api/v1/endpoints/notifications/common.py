"""
These endpoints work across ALL channels (email, push, sms, ...).
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant, get_db
from app.api.responses import ResponseMetaDep, success_response
from app.infrastructure.db.models import (
    NotificationChannel,
    NotificationStatus,
    Tenant,
)
from app.schemas.common import SuccessResponse
from app.schemas.notification import (
    NotificationRead,
)
from app.services.notification_service import NotificationService

router = APIRouter(tags=["notifications"])


# Helpers
def to_read(n) -> NotificationRead:
    """Build a NotificationRead from an ORM Notification."""
    return NotificationRead(
        id=n.id,
        tenant_id=n.tenant_id,
        user_id=n.user_id,
        user_external_id=n.user.external_id if n.user else None,
        channel=n.channel,
        title=n.title,
        body=n.body,
        payload=n.payload,
        status=n.status,
        attempts=n.attempts,
        last_error=n.last_error,
        created_at=n.created_at,
        updated_at=n.updated_at,
    )


# GET /notifications
@router.get(
    "/",
    response_model=SuccessResponse[list[NotificationRead]],
    summary="List notifications",
    description="Paginated list of notifications across all channels, newest first.",
)
async def list_notifications(
    meta: ResponseMetaDep,
    tenant: Tenant = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db),
    status_filter: NotificationStatus | None = Query(default=None, alias="status"),
    channel: NotificationChannel | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> SuccessResponse[list[NotificationRead]]:
    service = NotificationService()
    items, _total = await service.list_by_tenant(
        session,
        tenant,
        status=status_filter,
        channel=channel,
        limit=limit,
        offset=offset,
    )
    return success_response([to_read(n) for n in items], meta)


# GET /notifications/{notification_id}
@router.get(
    "/{notification_id}",
    response_model=SuccessResponse[NotificationRead],
    summary="Get a notification by ID",
)
async def get_notification(
    notification_id: UUID,
    meta: ResponseMetaDep,
    tenant: Tenant = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db),
) -> SuccessResponse[NotificationRead]:
    service = NotificationService()
    notification = await service.get_by_id(session, tenant, notification_id)
    return success_response(to_read(notification), meta)
