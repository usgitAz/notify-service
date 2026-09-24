"""
Middleware that assigns a correlation ID to every request.

The ID is taken from the inbound X-Request-ID header when present
(so callers can trace across services), otherwise generated fresh.
It is exposed both on `request.state.request_id` and echoed back
in the X-Request-ID response header.
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from typing import cast

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return cast(Response, response)


def get_request_id(request: Request) -> str | None:
    """Safe accessor for the request ID, usable anywhere in handlers."""
    return getattr(request.state, "request_id", None)
