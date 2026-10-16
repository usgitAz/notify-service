from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import Device, User
from app.repositories.base import BaseRepository


class DeviceRepository(BaseRepository[Device]):
    """Repository for Device."""

    model = Device

    async def get_active_by_id_and_tenant(
        self,
        session: AsyncSession,
        device_id: UUID,
        tenant_id: UUID,
    ) -> Device | None:
        """
        Fetch an active device by ID, ensuring it belongs to the tenant.

        Uses join with User for cross-tenant isolation.
        """
        stmt = (
            select(Device)
            .join(User, Device.user_id == User.id)
            .where(
                Device.id == device_id,
                Device.is_active.is_(True),
                User.tenant_id == tenant_id,
                User.is_active.is_(True),
            )
        )
        result = await session.scalars(stmt)
        return result.first()

    async def get_by_token(
        self,
        session: AsyncSession,
        token: str,
    ) -> Device | None:
        """Find a device by its token (globally unique)."""
        stmt = select(Device).where(Device.token == token)
        result = await session.scalars(stmt)
        return result.first()

    async def list_by_user(
        self,
        session: AsyncSession,
        user_id: UUID,
        *,
        is_active: bool | None = True,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Device], int]:
        """
        List devices of a user with pagination.

        Default is_active=True preserves previous API behavior (active only).
        Pass is_active=None for all devices.
        """
        conditions = [Device.user_id == user_id]
        if is_active is not None:
            conditions.append(Device.is_active.is_(is_active))

        base = select(Device).where(*conditions)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = await session.scalar(count_stmt) or 0

        stmt = base.order_by(Device.created_at.desc()).limit(limit).offset(offset)
        result = await session.scalars(stmt)
        return list(result), total

    async def count_active_by_user(
        self,
        session: AsyncSession,
        user_id: UUID,
    ) -> int:
        """Count active devices of a user."""
        stmt = (
            select(func.count())
            .select_from(Device)
            .where(
                Device.user_id == user_id,
                Device.is_active.is_(True),
            )
        )
        return await session.scalar(stmt) or 0
