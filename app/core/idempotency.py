"""
Design:
- Key format: `idempotency:{tenant_id}:{client_key}` (tenant-scoped).
- Value: JSON with `status_code` and `body`.
- TTL: from settings (default 24h).
- Fail-open: if Redis is unavailable (None) or errors, requests still proceed.
"""

from __future__ import annotations

import json
from typing import Any, cast
from uuid import UUID

import redis.asyncio as aioredis
from redis.exceptions import RedisError

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

PREFIX = "idempotency"


def build_key(tenant_id: UUID, client_key: str) -> str:
    """Build the Redis key for a given tenant + client key."""
    return f"{PREFIX}:{tenant_id}:{client_key}"


async def get_cached_response(
    redis: aioredis.Redis | None,
    key: str,
) -> dict[str, Any] | None:
    """
    Return the cached response for `key`, or None.
    (caller proceeds as if there were no cache).
    """
    if redis is None:
        return None

    try:
        raw = await redis.get(key)
    except RedisError as exc:
        logger.warning("idempotency_get_failed", key=key, error=str(exc))
        return None

    if raw is None:
        return None

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("idempotency_invalid_cache", key=key)
        return None

    if not isinstance(parsed, dict):
        logger.warning("idempotency_invalid_cache_shape", key=key)
        return None

    return cast(dict[str, Any], parsed)


async def cache_response(
    redis: aioredis.Redis | None,
    key: str,
    *,
    status_code: int,
    body: dict[str, Any],
) -> None:
    """
    Cache a response for idempotency.
    Uses SET with EX (TTL).
    """
    if redis is None:
        return

    payload = {
        "status_code": status_code,
        "body": body,
    }

    try:
        await redis.set(
            key,
            json.dumps(payload),
            ex=settings.idempotency_ttl_seconds,
        )
    except RedisError as exc:
        logger.warning("idempotency_cache_failed", key=key, error=str(exc))
        return

    logger.info(
        "idempotency_cached",
        key=key,
        status_code=status_code,
        ttl=settings.idempotency_ttl_seconds,
    )
