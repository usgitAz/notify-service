"""OpenAPI spec regression tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestOpenAPISecurityScheme:
    async def test_api_key_header_scheme_is_declared(self, client: AsyncClient):
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        spec = response.json()

        schemes = spec["components"]["securitySchemes"]
        assert "APIKeyHeader" in schemes
        assert schemes["APIKeyHeader"]["type"] == "apiKey"
        assert schemes["APIKeyHeader"]["in"] == "header"
        assert schemes["APIKeyHeader"]["name"] == "X-API-Key"

    async def test_protected_endpoint_requires_api_key(self, client: AsyncClient):
        """Users POST must declare security in OpenAPI."""
        response = await client.get("/openapi.json")
        spec = response.json()

        post_users = spec["paths"]["/api/v1/users"]["post"]
        assert post_users.get("security") == [{"APIKeyHeader": []}]

    async def test_health_endpoints_are_public(self, client: AsyncClient):
        """Health endpoints must NOT require auth."""
        response = await client.get("/openapi.json")
        spec = response.json()

        health = spec["paths"]["/health"]["get"]
        assert "security" not in health
        assert health.get("security", []) == []
