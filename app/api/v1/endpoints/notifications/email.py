"""
POST /api/v1/notifications/email
    Create an email notification for a user.
    Delivery is asynchronous (BackgroundTasks).
    Supports Idempotency-Key.
"""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    IdempotencyKeyDep,
    RedisDep,
    get_current_tenant,
    get_db,
)
from app.api.responses import ResponseMetaDep, success_response
from app.api.v1.endpoints.notifications.common import to_read
from app.core.idempotency import build_key, cache_response, get_cached_response
from app.core.logging import get_logger
from app.infrastructure.db.models import Tenant
from app.schemas.common import SuccessResponse
from app.schemas.notification import (
    NotificationEmailCreate,
    NotificationRead,
)
from app.services.notification_email_service import NotificationEmailService
from app.services.notification_service import NotificationService
from app.services.sender import send_notification

logger = get_logger(__name__)

router = APIRouter(tags=["notifications"])


@router.post(
    "/email",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=SuccessResponse[NotificationRead],
    summary="Send an email notification",
    description=(
        "Create an email notification for a user. "
        "The user must have an email address. "
        "Returns 202 Accepted; delivery is asynchronous. "
        "Send an `Idempotency-Key` header to make retries safe."
    ),
)
async def create_email_notification(
    request: NotificationEmailCreate,
    background: BackgroundTasks,
    meta: ResponseMetaDep,
    tenant: Tenant = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db),
    redis: RedisDep = None,
    idempotency_key: IdempotencyKeyDep = None,
) -> JSONResponse | SuccessResponse[NotificationRead]:
    # 1. Idempotency check (if key provided)
    idem_redis_key: str | None = None
    if idempotency_key:
        idem_redis_key = build_key(tenant.id, idempotency_key)
        cached = await get_cached_response(redis, idem_redis_key)
        if cached is not None:
            logger.info(
                "idempotency_hit",
                key=idem_redis_key,
                tenant_id=str(tenant.id),
            )
            return JSONResponse(
                status_code=cached["status_code"],
                content=cached["body"],
            )

    # 2. Create the notification
    service = NotificationEmailService()
    notification = await service.create_email(session, tenant, request)
    await session.commit()

    # 3. Schedule delivery
    background.add_task(send_notification, str(notification.id))

    # 4. Build response
    shared = NotificationService()
    full = await shared.get_by_id(session, tenant, notification.id)
    response = success_response(to_read(full), meta)

    # 5. Cache for idempotency
    if idem_redis_key:
        await cache_response(
            redis,
            idem_redis_key,
            status_code=status.HTTP_202_ACCEPTED,
            body=response.model_dump(mode="json"),
        )

    return response
