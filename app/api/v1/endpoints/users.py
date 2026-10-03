from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant, get_db
from app.api.responses import ResponseMetaDep, success_response
from app.infrastructure.db.models import Tenant
from app.schemas.common import SuccessResponse
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse[UserRead],
    summary="Create a user",
    description=(
        "Create a new user belonging to the authenticated tenant. "
        "`external_id` must be unique within the tenant."
    ),
)
async def create_user(
    request: UserCreate,
    meta: ResponseMetaDep,
    tenant: Tenant = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db),
) -> SuccessResponse[UserRead]:
    service = UserService()
    user = await service.create(session, tenant, request)
    await session.commit()
    return success_response(UserRead.model_validate(user), meta)


@router.get(
    "/{external_id}",
    response_model=SuccessResponse[UserRead],
    summary="Get a user by external_id",
)
async def get_user(
    external_id: str,
    meta: ResponseMetaDep,
    tenant: Tenant = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db),
) -> SuccessResponse[UserRead]:
    service = UserService()
    user = await service.get_by_external_id(session, tenant, external_id)
    return success_response(UserRead.model_validate(user), meta)


@router.patch(
    "/{external_id}",
    response_model=SuccessResponse[UserRead],
    summary="Update a user",
    description=(
        "Partial update. Currently supports `email` and `is_active`. "
        "Setting `is_active=false` performs a soft delete."
    ),
)
async def update_user(
    external_id: str,
    request: UserUpdate,
    meta: ResponseMetaDep,
    tenant: Tenant = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db),
) -> SuccessResponse[UserRead]:
    service = UserService()
    user = await service.update(session, tenant, external_id, request)
    await session.commit()
    return success_response(UserRead.model_validate(user), meta)
