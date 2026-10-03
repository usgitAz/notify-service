"""
POST /api/v1/notifications/email
    Create an email notification for a user.
    Delivery is asynchronous (BackgroundTasks).
"""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant, get_db
from app.api.responses import ResponseMetaDep, success_response
from app.api.v1.endpoints.notifications.common import to_read
from app.infrastructure.db.models import Tenant
from app.schemas.common import SuccessResponse
from app.schemas.notification import (
    NotificationEmailCreate,
    NotificationRead,
)
from app.services.notification_email_service import NotificationEmailService
from app.services.notification_service import NotificationService
from app.services.sender import send_notification

router = APIRouter(tags=["notifications"])


@router.post(
    "/email",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=SuccessResponse[NotificationRead],
    summary="Send an email notification",
    description=(
        "Create an email notification for a user. "
        "The user must have an email address. "
        "Returns 202 Accepted; delivery is asynchronous."
    ),
)
async def create_email_notification(
    request: NotificationEmailCreate,
    background: BackgroundTasks,
    meta: ResponseMetaDep,
    tenant: Tenant = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db),
) -> SuccessResponse[NotificationRead]:
    # 1. Create the notification record
    service = NotificationEmailService()
    notification = await service.create_email(session, tenant, request)
    await session.commit()

    # 2. Schedule delivery in the background
    background.add_task(send_notification, str(notification.id))

    # 3. Reload with user eager-loaded for the response
    shared = NotificationService()
    full = await shared.get_by_id(session, tenant, notification.id)
    return success_response(to_read(full), meta)
