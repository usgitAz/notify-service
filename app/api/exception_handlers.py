"""
Global exception handlers.

Contract:
- Every error response has the exact shape of ErrorResponse.
- Internal details (tracebacks, DB errors) never leave the process.
- Each error is logged with enough context to correlate with request_id.

Typing note:
Starlette's `add_exception_handler` is typed as accepting
`Callable[[Request, Exception], ...]`. To satisfy mypy, every handler
below declares `exc: Exception` and narrows to the concrete type at
runtime via `isinstance`. This is the officially recommended workaround
and has zero runtime cost since Starlette only dispatches handlers
matching the registered exception class.
"""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppBaseException
from app.core.logging import get_logger  # fapilog-based logger
from app.middleware.request_id import get_request_id
from app.schemas.common import ErrorBody, ErrorDetail, ErrorResponse, ResponseMeta

logger = get_logger(__name__)


# Helpers


def _build_error_response(
    *,
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: list[ErrorDetail] | None = None,
) -> JSONResponse:
    """Single place that knows how to serialize an ErrorResponse."""
    payload = ErrorResponse(
        error=ErrorBody(code=code, message=message, details=details),
        meta=ResponseMeta(request_id=get_request_id(request)),
    )
    return JSONResponse(
        status_code=status_code, content=payload.model_dump(mode="json")
    )


# Handlers


async def app_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handles every domain exception raised anywhere in the app.

    Narrowed to AppBaseException at runtime. If somehow a different
    exception reaches here, we fall back to a safe 500.
    """
    if not isinstance(exc, AppBaseException):
        # Defensive: should never happen given registration in
        # register_exception_handlers(). Treat as unexpected.
        return await unhandled_exception_handler(request, exc)

    logger.warning(
        "Domain exception",
        extra={
            "error_code": exc.code,
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
            "request_id": get_request_id(request),
            "details": [d.model_dump() for d in exc.details] if exc.details else None,
        },
    )
    return _build_error_response(
        request=request,
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        details=exc.details,
    )


async def validation_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """
    Normalizes Pydantic/FastAPI validation errors into our ErrorResponse shape.

    Note: `loc` may start with 'body', 'query', 'path', or 'header'.
    We preserve that prefix so clients know *where* the field lives.
    """
    if not isinstance(exc, RequestValidationError):
        return await unhandled_exception_handler(request, exc)

    details: list[ErrorDetail] = []
    for err in exc.errors():
        loc = err.get("loc", ())
        field = ".".join(str(part) for part in loc) or None
        details.append(
            ErrorDetail(
                field=field,
                code=err.get("type"),
                message=err.get("msg", "Invalid value."),
            )
        )

    logger.warning(
        "Request validation failed",
        extra={
            "path": request.url.path,
            "method": request.method,
            "request_id": get_request_id(request),
            "error_count": len(details),
        },
    )
    return _build_error_response(
        request=request,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        code="VALIDATION_ERROR",
        message="Request data failed validation.",
        details=details,
    )


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Wraps Starlette's HTTPException (raised internally by FastAPI, e.g. 405)
    so it also conforms to ErrorResponse.
    """
    if not isinstance(exc, StarletteHTTPException):
        return await unhandled_exception_handler(request, exc)

    return _build_error_response(
        request=request,
        status_code=exc.status_code,
        code=f"HTTP_{exc.status_code}",
        message=str(exc.detail),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all. Logs full traceback server-side, returns an opaque 500.
    Never leak exception type or message to the client in production.
    """
    logger.exception(
        "Unhandled exception",
        extra={
            "path": request.url.path,
            "method": request.method,
            "request_id": get_request_id(request),
            "exception_type": type(exc).__name__,
        },
    )
    return _build_error_response(
        request=request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred. Please try again later.",
    )


# Registration


def register_exception_handlers(app: FastAPI) -> None:
    """Wire all handlers onto the FastAPI app. Call once from main.py."""
    app.add_exception_handler(AppBaseException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
