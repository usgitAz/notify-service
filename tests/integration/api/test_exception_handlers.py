"""Integration tests for exception handlers (HTTP-level)."""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestExceptionHandlers:
    async def test_404_via_http_exception(self, client: AsyncClient, auth_headers):
        response = await client.get("/api/v1/nonexistent", headers=auth_headers)
        assert response.status_code == 404
        body = response.json()
        assert body["success"] is False
        assert "error" in body
        assert "meta" in body

    async def test_405_method_not_allowed(self, client: AsyncClient, auth_headers):
        response = await client.delete("/api/v1/users/xx", headers=auth_headers)
        assert response.status_code == 405

    async def test_validation_error(self, client: AsyncClient, auth_headers):
        response = await client.post(
            "/api/v1/users", headers=auth_headers, json={"external_id": ""}
        )
        assert response.status_code == 422
        body = response.json()
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert body["error"]["details"] is not None
