from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant, get_db
from app.api.responses import ResponseMetaDep, success_response
from app.infrastructure.db.models import Tenant
from app.schemas.common import SuccessResponse
from app.schemas.device import DeviceCreate, DeviceRead, DeviceUpdate
from app.services.device_service import DeviceService
from app.services.user_service import UserService

router = APIRouter(tags=["devices"])


# Devices under a user
@router.post(
    "/users/{external_id}/device/register",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse[DeviceRead],
    summary="Register a device for a user",
    description=(
        "Register a new push device for the given user. "
        "`token` must be globally unique. "
        "If the token is already registered to the same user and inactive, "
        "it will be reactivated."
    ),
)
async def register_device(
    external_id: str,
    request: DeviceCreate,
    meta: ResponseMetaDep,
    tenant: Tenant = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db),
) -> SuccessResponse[DeviceRead]:
    user = await UserService().get_by_external_id(session, tenant, external_id)
    device = await DeviceService().register(session, user, request)
    await session.commit()
    return success_response(DeviceRead.model_validate(device), meta)


@router.get(
    "/users/{external_id}/devices",
    response_model=SuccessResponse[list[DeviceRead]],
    summary="List a user's devices",
    description="List all active devices of the given user.",
)
async def list_devices(
    external_id: str,
    meta: ResponseMetaDep,
    tenant: Tenant = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db),
) -> SuccessResponse[list[DeviceRead]]:
    user = await UserService().get_by_external_id(session, tenant, external_id)
    devices = await DeviceService().list_by_user(session, user)
    return success_response(
        [DeviceRead.model_validate(d) for d in devices],
        meta,
    )


# Device by ID
@router.get(
    "/devices/{device_id}",
    response_model=SuccessResponse[DeviceRead],
    summary="Get a device by ID",
    description="Fetch a single active device, scoped to the authenticated tenant.",
)
async def get_device(
    device_id: UUID,
    meta: ResponseMetaDep,
    tenant: Tenant = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db),
) -> SuccessResponse[DeviceRead]:
    device = await DeviceService().get_by_id(session, tenant, device_id)
    return success_response(DeviceRead.model_validate(device), meta)


@router.patch(
    "/devices/{device_id}",
    response_model=SuccessResponse[DeviceRead],
    summary="Update a device",
    description=(
        "Partial update. Supports `device_name` and `is_active`. "
        "Setting `is_active=false` deactivates the device (e.g., on logout). "
        "There is no hard delete."
    ),
)
async def update_device(
    device_id: UUID,
    request: DeviceUpdate,
    meta: ResponseMetaDep,
    tenant: Tenant = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db),
) -> SuccessResponse[DeviceRead]:
    device = await DeviceService().update(session, tenant, device_id, request)
    await session.commit()
    return success_response(DeviceRead.model_validate(device), meta)
