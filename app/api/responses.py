"""
HTTP response helpers.

Provides:
- success_response: wraps a payload in a SuccessResponse envelope.
- ResponseMetaDep: FastAPI dependency that injects ResponseMeta.

Why a helper instead of middleware:
- Explicit at the call site.
- Type-safe: return type is SuccessResponse[T].
- OpenAPI schema is generated correctly.
"""

from __future__ import annotations

from typing import Annotated, TypeVar

from fastapi import Depends

from app.api.deps import get_response_meta
from app.schemas.common import ResponseMeta, SuccessResponse

T = TypeVar("T")


def success_response[T](
    data: T,
    meta: ResponseMeta,
) -> SuccessResponse[T]:
    """
    Wrap `data` in a SuccessResponse envelope.

    Usage:
        return success_response(UserRead.model_validate(user), meta)
    """
    return SuccessResponse(data=data, meta=meta)


# FastAPI dependency: injects ResponseMeta (with request_id) into handlers.
ResponseMetaDep = Annotated[ResponseMeta, Depends(get_response_meta)]
