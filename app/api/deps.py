from collections.abc import AsyncGenerator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.session import AsyncSessionLocal
from app.middleware.request_id import get_request_id
from app.schemas.common import ResponseMeta


async def get_db() -> AsyncGenerator[AsyncSession]:
    """Yield an async db session , rollback on error."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except:
            await session.rollback()
            raise


def get_response_meta(request: Request) -> ResponseMeta:
    """Dependency that builds ResponseMeta with the current request_id."""
    return ResponseMeta(request_id=get_request_id(request))
