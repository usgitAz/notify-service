from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_external_id(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        external_id: str,
    ) -> User | None:
        """Find an active user by (tenant_id, external_id)."""
        stmt = select(User).where(
            User.tenant_id == tenant_id,
            User.external_id == external_id,
            User.is_active.is_(True),
        )
        result = await session.scalars(stmt)
        return result.first()  # pragma: no cover

    async def list_by_tenant(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[User], int]:
        """List active users of a tenant with pagination."""
        base = select(User).where(
            User.tenant_id == tenant_id,
            User.is_active.is_(True),
        )

        # total count (separate query, no limit)
        from sqlalchemy import func

        count_stmt = select(func.count()).select_from(base.subquery())
        total = await session.scalar(count_stmt) or 0

        # data
        stmt = base.order_by(User.created_at.desc()).limit(limit).offset(offset)
        result = await session.scalars(stmt)
        items = list(result)

        return items, total

    async def get_by_external_id_any(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        external_id: str,
    ) -> User | None:
        """Fetch regardless of is_active (for reactivation)."""
        stmt = select(User).where(
            User.tenant_id == tenant_id,
            User.external_id == external_id,
        )
        result = await session.scalars(stmt)
        return result.first()  # pragma: no cover
