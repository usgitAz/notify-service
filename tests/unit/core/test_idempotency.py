"""Unit tests for app.core.idempotency."""

from uuid import uuid4

import pytest

from app.core.idempotency import (
    build_key,
    cache_response,
    get_cached_response,
)


@pytest.mark.unit
class TestBuildKey:
    def test_format(self):
        tenant_id = uuid4()
        key = build_key(tenant_id, "abc")
        assert key == f"idempotency:{tenant_id}:abc"

    def test_different_tenants_different_keys(self):
        k1 = build_key(uuid4(), "same")
        k2 = build_key(uuid4(), "same")
        assert k1 != k2


@pytest.mark.unit
class TestGetCachedResponse:
    async def test_none_redis(self):
        assert await get_cached_response(None, "any") is None

    async def test_cache_miss(self, redis_client):
        assert await get_cached_response(redis_client, "missing") is None

    async def test_cache_hit(self, redis_client):
        await cache_response(
            redis_client,
            "k1",
            status_code=202,
            body={"foo": "bar"},
        )
        result = await get_cached_response(redis_client, "k1")
        assert result == {"status_code": 202, "body": {"foo": "bar"}}

    async def test_invalid_json(self, redis_client):
        await redis_client.set("bad", "not-json")
        assert await get_cached_response(redis_client, "bad") is None

    async def test_non_dict_json(self, redis_client):
        await redis_client.set("arr", "[1, 2, 3]")
        assert await get_cached_response(redis_client, "arr") is None


@pytest.mark.unit
class TestCacheResponse:
    async def test_none_redis_no_op(self):
        # Should not raise
        await cache_response(None, "any", status_code=200, body={})

    async def test_sets_ttl(self, redis_client):
        await cache_response(redis_client, "k", status_code=200, body={"a": 1})
        ttl = await redis_client.ttl("k")
        assert ttl > 0


class TestRedisErrors:
    async def test_get_redis_error_returns_none(self, redis_client):
        """Simulate RedisError → returns None."""
        from unittest.mock import AsyncMock, patch

        from redis.exceptions import RedisError

        with patch.object(
            redis_client,
            "get",
            new_callable=AsyncMock,
            side_effect=RedisError("boom"),
        ):
            result = await get_cached_response(redis_client, "any")
            assert result is None

    async def test_set_redis_error_silently_fails(self, redis_client):
        """Simulate RedisError on set → no exception raised."""
        from unittest.mock import AsyncMock, patch

        from redis.exceptions import RedisError

        with patch.object(
            redis_client,
            "set",
            new_callable=AsyncMock,
            side_effect=RedisError("boom"),
        ):
            # Should not raise
            await cache_response(redis_client, "k", status_code=200, body={})
