from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.infrastructure.db.models import Device, Tenant, User
from app.repositories.device_repo import DeviceRepository
from app.schemas.device import DeviceCreate, DeviceUpdate


class DeviceService:
    """Service for Device operations."""

    def __init__(self) -> None:
        self.repo = DeviceRepository()

    async def register(
        self,
        session: AsyncSession,
        user: User,
        payload: DeviceCreate,
    ) -> Device:
        """
        Register a new device for a user.

        Rules:
        - `token` must be globally unique.
        - If the same token is already registered to ANOTHER user,
          reject with 409.
        - If the same token is registered to THIS user and is inactive,
          reactivate it (idempotent).
        """
        existing = await self.repo.get_by_token(session, payload.token)
        if existing is not None:
            if existing.user_id != user.id:
                raise ConflictError(
                    "This device token is already registered to another user.",
                    code="DEVICE_TOKEN_TAKEN",
                )
            if existing.is_active:
                raise ConflictError(
                    "This device token is already registered.",
                    code="DEVICE_ALREADY_REGISTERED",
                )
            # Reactivate: same token, same user, currently inactive
            existing.is_active = True
            existing.deactivated_at = None
            existing.platform = payload.platform
            existing.provider = payload.provider
            existing.device_name = payload.device_name
            await session.flush()
            await session.refresh(existing)
            return existing

        device = Device(
            user_id=user.id,
            platform=payload.platform,
            provider=payload.provider,
            token=payload.token,
            device_name=payload.device_name,
        )
        await self.repo.add(session, device)
        return device

    async def list_by_user(
        self,
        session: AsyncSession,
        user: User,
    ) -> list[Device]:
        """List all active devices of a user."""
        return await self.repo.list_active_by_user(session, user.id)

    async def get_by_id(
        self,
        session: AsyncSession,
        tenant: Tenant,
        device_id: UUID,
    ) -> Device:
        """Fetch an active device by ID, scoped to the tenant."""
        device = await self.repo.get_active_by_id_and_tenant(
            session, device_id, tenant.id
        )
        if device is None:
            raise NotFoundError(
                f"Device '{device_id}' not found.",
                code="DEVICE_NOT_FOUND",
            )
        return device

    async def update(
        self,
        session: AsyncSession,
        tenant: Tenant,
        device_id: UUID,
        payload: DeviceUpdate,
    ) -> Device:
        """
        Update a device (device_name, is_active).

        Setting `is_active=false` deactivates the device
        (e.g., on logout). There is no hard delete.
        """
        device = await self.get_by_id(session, tenant, device_id)

        if payload.device_name is not None:
            device.device_name = payload.device_name

        if payload.is_active is False:
            device.is_active = False
            device.deactivated_at = datetime.now(UTC)

        await session.flush()
        await session.refresh(device)
        return device
