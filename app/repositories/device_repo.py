from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import Device, DevicePlatform, User
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

    async def list_active_by_user(
        self,
        session: AsyncSession,
        user_id: UUID,
        *,
        platform: DevicePlatform | None = None,
    ) -> list[Device]:
        """List active devices of a user, optionally filtered by platform."""
        stmt = select(Device).where(
            Device.user_id == user_id,
            Device.is_active.is_(True),
        )
        if platform is not None:
            stmt = stmt.where(Device.platform == platform)
        stmt = stmt.order_by(Device.created_at.desc())
        result = await session.scalars(stmt)
        return list(result)

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
