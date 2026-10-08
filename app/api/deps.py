"""
FastAPI dependencies.

- get_db: yields an async DB session.
- get_response_meta: builds ResponseMeta with request_id.
- get_current_tenant: validates X-API-Key and returns the Tenant.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

import redis.asyncio as aioredis
from fastapi import Depends, Header, Request, Security
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.security import api_key_header
from app.core.exceptions import AuthenticationError
from app.core.redis import redis_client
from app.core.security import extract_prefix, verify_api_key
from app.infrastructure.db.models import Tenant
from app.infrastructure.db.session import AsyncSessionLocal
from app.middleware.request_id import get_request_id
from app.repositories.tenant_repo import TenantRepository
from app.schemas.common import ResponseMeta

# Constant error message to avoid leaking which step failed.
_INVALID_KEY_MSG = "Invalid or missing API key."


async def get_db() -> AsyncGenerator[AsyncSession]:
    """Yield an async DB session, rollback on error."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


def get_response_meta(request: Request) -> ResponseMeta:
    """Build ResponseMeta with the current request_id."""
    return ResponseMeta(request_id=get_request_id(request))


async def get_current_tenant(
    session: Annotated[AsyncSession, Depends(get_db)],
    api_key: Annotated[
        str | None,
        Security(api_key_header),
    ] = None,
) -> Tenant:
    """
    Validate the X-API-Key header and return the owning Tenant.

    Security notes:
    - All failure modes return the SAME 401 error message.
    - Prefix lookup is O(1) (indexed).
    - Hash comparison is constant-time (hmac.compare_digest).
    """
    # 1. Header present?
    if not api_key:
        raise AuthenticationError(_INVALID_KEY_MSG)

    # 2. Basic format sanity (sk_<env>_<random>)
    if not api_key.startswith("sk_") or api_key.count("_") < 2:
        raise AuthenticationError(_INVALID_KEY_MSG)

    # 3. Extract prefix and look up tenant
    prefix = extract_prefix(api_key)
    repo = TenantRepository()
    tenant = await repo.get_by_api_key_prefix(session, prefix)

    # 4. Constant response for "not found"
    if tenant is None:
        raise AuthenticationError(_INVALID_KEY_MSG)

    # 5. Verify the full key against the stored hash
    if not verify_api_key(api_key, tenant.api_key_hash):
        raise AuthenticationError(_INVALID_KEY_MSG)

    return tenant


# Idempotency
async def get_idempotency_key(
    idempotency_key: Annotated[
        str | None,
        Header(
            alias="Idempotency-Key",
            description=(
                "Client-generated unique key. "
                "Recommended: UUID v4. "
                "Max length: 255. "
                "Retries with the same key return the original response."
            ),
            min_length=1,
            max_length=255,
        ),
    ] = None,
) -> str | None:
    """Extract and validate the Idempotency-Key header."""
    return idempotency_key


IdempotencyKeyDep = Annotated[str | None, Depends(get_idempotency_key)]


def get_redis() -> aioredis.Redis | None:
    """Return the shared Redis client, or None if unavailable."""
    return redis_client


RedisDep = Annotated[aioredis.Redis | None, Depends(get_redis)]
