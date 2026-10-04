"""
Redis client (async).

Used for:
- Idempotency keys (later phases may add rate limiting, caching, ...).
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import redis.asyncio as aioredis

from app.core.config import settings

# Global Redis client (connection pool managed internally)
redis_client: aioredis.Redis = aioredis.from_url(
    settings.redis_url,
    encoding="utf-8",
    decode_responses=True,  # → str, not bytes
)


async def get_redis() -> AsyncGenerator[aioredis.Redis]:
    """
    FastAPI dependency.

    In practice we reuse the global client (with a pool);
    this generator exists for symmetry with `get_db`.
    """
    yield redis_client
