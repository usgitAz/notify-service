"""Unit tests for exception handlers.

Handlers are called directly to verify response shape and defensive
branches. HTTP-level behavior (routing, middleware) is covered in
tests/integration/api/test_exception_handlers.py.
"""

import json

import pytest
from starlette.requests import Request

from app.api.exception_handlers import unhandled_exception_handler


def _make_request(path: str = "/test", method: str = "GET") -> Request:
    """Build a minimal Starlette Request for handler invocation."""
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "headers": [],
        "query_string": b"",
    }
    return Request(scope)


@pytest.mark.unit
class TestUnhandledExceptionHandler:
    async def test_returns_500_with_generic_message(self):
        request = _make_request(path="/boom", method="POST")
        exc = RuntimeError("boom-internal")

        response = await unhandled_exception_handler(request, exc)

        assert response.status_code == 500
        body = json.loads(response.body)
        assert body["success"] is False
        assert body["error"]["code"] == "INTERNAL_SERVER_ERROR"
        assert body["error"]["message"] == (
            "An unexpected error occurred. Please try again later."
        )

    async def test_does_not_leak_internal_details(self):
        request = _make_request()
        exc = RuntimeError("db password leaked at line 42")

        response = await unhandled_exception_handler(request, exc)
        body = json.loads(response.body)

        assert "password" not in body["error"]["message"].lower()
        assert "RuntimeError" not in body["error"]["message"]
        assert "line 42" not in body["error"]["message"]

    async def test_body_has_error_and_meta(self):
        request = _make_request()
        response = await unhandled_exception_handler(request, RuntimeError("x"))
        body = json.loads(response.body)
        assert "error" in body
        assert "meta" in body
        assert body["meta"]["request_id"] is None
