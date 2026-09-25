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
    NotificationCreate,
    NotificationListFilters,
    NotificationRead,
)
from app.schemas.user import UserCreate, UserRead

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
    # User
    "UserCreate",
    "UserRead",
    # Device
    "DeviceCreate",
    "DeviceUpdate",
    "DeviceRead",
    # Notification
    "NotificationCreate",
    "NotificationRead",
    "NotificationListFilters",
]
