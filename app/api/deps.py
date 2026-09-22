from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.session import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession]:
    """Yield an async db session , rollback on error."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except:
            await session.rollback()
            raise
