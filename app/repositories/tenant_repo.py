"""Tenant repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import Tenant
from app.repositories.base import BaseRepository


class TenantRepository(BaseRepository[Tenant]):
    """Repository for Tenant."""

    model = Tenant

    async def get_by_name(
        self,
        session: AsyncSession,
        name: str,
    ) -> Tenant | None:
        """Find an active tenant by exact name."""
        stmt = select(Tenant).where(
            Tenant.name == name,
            Tenant.is_active.is_(True),
        )
        result = await session.scalars(stmt)
        return result.first()

    async def get_by_api_key_prefix(
        self,
        session: AsyncSession,
        prefix: str,
    ) -> Tenant | None:
        """Find an active tenant by API key prefix (indexed)."""
        stmt = select(Tenant).where(
            Tenant.api_key_prefix == prefix,
            Tenant.is_active.is_(True),
        )
        result = await session.scalars(stmt)
        return result.first()
