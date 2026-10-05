"""Integration tests for exception handlers."""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestExceptionHandlers:
    async def test_404_via_http_exception(self, client: AsyncClient, auth_headers):
        """HTTPException from Starlette → ErrorResponse shape."""
        response = await client.get("/api/v1/nonexistent", headers=auth_headers)
        assert response.status_code == 404
        body = response.json()
        assert body["success"] is False
        assert "error" in body
        assert "meta" in body

    async def test_405_method_not_allowed(self, client: AsyncClient, auth_headers):
        """StarletteHTTPException with 405."""
        response = await client.patch("/api/v1/users/xx", headers=auth_headers, json={})
        # PATCH is allowed; test a method that isn't
        response = await client.delete("/api/v1/users/xx", headers=auth_headers)
        assert response.status_code == 405

    async def test_validation_error(self, client: AsyncClient, auth_headers):
        """RequestValidationError → 422 with details."""
        response = await client.post(
            "/api/v1/users", headers=auth_headers, json={"external_id": ""}
        )
        assert response.status_code == 422
        body = response.json()
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert body["error"]["details"] is not None

    async def test_unhandled_exception_returns_500(
        self, client: AsyncClient, auth_headers, monkeypatch
    ):
        """Unhandled exception → 500 with generic message."""
        from unittest.mock import AsyncMock, patch

        from app.api.v1.endpoints import users as users_endpoint

        with patch.object(
            users_endpoint.UserService,
            "create",
            new_callable=AsyncMock,
            side_effect=RuntimeError("boom"),
        ):
            response = await client.post(
                "/api/v1/users",
                headers=auth_headers,
                json={"external_id": "x", "email": "x@y.com"},
            )
            assert response.status_code == 500
            body = response.json()
            assert body["error"]["code"] == "INTERNAL_SERVER_ERROR"
            assert "traceback" not in body["error"]["message"].lower()
