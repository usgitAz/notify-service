"""
Schemas package public API.
"""

from app.schemas.base import BaseRequest, BaseResponse, BaseSchema
from app.schemas.common import (
    ErrorBody,
    ErrorDetail,
    ErrorResponse,
    ResponseMeta,
    SuccessResponse,
)
from app.schemas.device import DeviceCreate, DeviceRead, DeviceUpdate
from app.schemas.notification import (
    NotificationEmailCreate,
    NotificationListFilters,
    NotificationRead,
)
from app.schemas.tenant import TenantCreate, TenantRead, TenantWithApiKey
from app.schemas.user import UserCreate, UserRead, UserUpdate

__all__ = [
    # Base
    "BaseSchema",
    "BaseRequest",
    "BaseResponse",
    # Common
    "SuccessResponse",
    "ErrorResponse",
    "ErrorBody",
    "ErrorDetail",
    "ResponseMeta",
    # Tenant
    "TenantCreate",
    "TenantRead",
    "TenantWithApiKey",
    # User
    "UserCreate",
    "UserRead",
    "UserUpdate",
    # Device
    "DeviceCreate",
    "DeviceUpdate",
    "DeviceRead",
    # Notification
    "NotificationRead",
    "NotificationListFilters",
    "NotificationEmailCreate",
]
