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
        is_active: bool | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[User], int]:
        """List users of a tenant with optional is_active filter and pagination."""
        from sqlalchemy import func

        conditions = [User.tenant_id == tenant_id]
        if is_active is not None:
            conditions.append(User.is_active.is_(is_active))

        base = select(User).where(*conditions)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = await session.scalar(count_stmt) or 0

        stmt = base.order_by(User.created_at.desc()).limit(limit).offset(offset)
        result = await session.scalars(stmt)
        return list(result), total

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
