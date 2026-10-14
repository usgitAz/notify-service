"""
Authentication endpoints.

Provides `/auth/me` so clients (dashboards, API consumers) can
validate their API key and fetch the owning tenant in a single call.
"""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_tenant
from app.api.openapi import RESPONSES_AUTHENTICATED
from app.api.responses import ResponseMetaDep, success_response
from app.infrastructure.db.models import Tenant
from app.schemas.common import SuccessResponse
from app.schemas.tenant import TenantRead

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses=RESPONSES_AUTHENTICATED,
)


@router.get(
    "/me",
    response_model=SuccessResponse[TenantRead],
    summary="Get the current tenant",
    description=(
        "Validate the API key and return the owning tenant. "
        "Use this to authenticate a client and display tenant info "
    ),
)
async def get_current_tenant_info(
    meta: ResponseMetaDep,
    tenant: Tenant = Depends(get_current_tenant),
) -> SuccessResponse[TenantRead]:
    """Return the authenticated tenant."""
    return success_response(TenantRead.model_validate(tenant), meta)
