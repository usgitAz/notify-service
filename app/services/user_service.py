from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.infrastructure.db.models import Tenant, User
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    """Service for User operations."""

    def __init__(self) -> None:
        self.repo = UserRepository()

    async def create(
        self,
        session: AsyncSession,
        tenant: Tenant,
        request: UserCreate,
    ) -> User:
        """
        Create a new user for the given tenant.

        The `(tenant_id, external_id)` pair must be unique across
        BOTH active and inactive records. If an inactive user with
        the same external_id exists, the client is instructed to
        reactivate via PATCH.
        """
        existing = await self.repo.get_by_external_id_any(
            session, tenant.id, request.external_id
        )
        if existing is not None:
            if existing.is_active:
                raise ConflictError(
                    f"User '{request.external_id}' already exists.",
                    code="USER_ALREADY_EXISTS",
                )
            raise ConflictError(
                f"User '{request.external_id}' exists but is inactive. "
                f"Reactivate it with PATCH /users/{request.external_id}.",
                code="USER_EXISTS_INACTIVE",
            )

        user = User(
            tenant_id=tenant.id,
            external_id=request.external_id,
            email=request.email,
        )
        await self.repo.add(session, user)
        return user

    async def get_by_external_id(
        self,
        session: AsyncSession,
        tenant: Tenant,
        external_id: str,
    ) -> User:
        """Fetch an active user by external_id, or raise NotFoundError."""
        user = await self.repo.get_by_external_id(session, tenant.id, external_id)
        if user is None:
            raise NotFoundError(
                f"User '{external_id}' not found.",
                code="USER_NOT_FOUND",
            )
        return user

    async def update(
        self,
        session: AsyncSession,
        tenant: Tenant,
        external_id: str,
        request: UserUpdate,
    ) -> User:
        """
        Update a user (email and/or is_active).

        Soft delete: `is_active=false`.
        Reactivation: `is_active=true` (idempotent).
        """
        user = await self.repo.get_by_external_id_any(session, tenant.id, external_id)
        if user is None:
            raise NotFoundError(
                f"User '{external_id}' not found.",
                code="USER_NOT_FOUND",
            )

        if request.email is not None:
            user.email = request.email

        if request.is_active is not None and request.is_active != user.is_active:
            user.is_active = request.is_active
            user.deactivated_at = None if request.is_active else datetime.now(UTC)

        await session.flush()
        await session.refresh(user)
        return user
