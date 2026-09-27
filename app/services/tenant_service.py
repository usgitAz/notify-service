"""Tenant service."""

from __future__ import annotations

from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError
from app.core.security import (
    extract_prefix,
    generate_api_key,
    hash_api_key,
)
from app.infrastructure.db.models import Tenant
from app.repositories.tenant_repo import TenantRepository
from app.schemas.tenant import TenantCreate, TenantRead, TenantWithApiKey


class TenantService:
    """Service for Tenant operations."""

    def __init__(self) -> None:
        self.repo = TenantRepository()

    async def register(
        self,
        session: AsyncSession,
        payload: TenantCreate,
        *,
        environment: Literal["live", "test"] = "live",
    ) -> TenantWithApiKey:
        """
        Register a new tenant and return it with a fresh API key.

        Steps:
          1. Ensure name is not taken.
          2. Generate a raw API key.
          3. Hash + prefix it.
          4. Persist the tenant.
          5. Return the raw key ONCE.
        """
        existing = await self.repo.get_by_name(session, payload.name)
        if existing is not None:
            raise ConflictError(
                f"Tenant with name '{payload.name}' already exists.",
                code="TENANT_NAME_TAKEN",
            )

        raw_key = generate_api_key(environment=environment)
        key_hash = hash_api_key(raw_key)
        key_prefix = extract_prefix(raw_key)

        tenant = Tenant(
            name=payload.name,
            api_key_hash=key_hash,
            api_key_prefix=key_prefix,
        )
        await self.repo.add(session, tenant)

        return TenantWithApiKey(
            tenant=TenantRead.model_validate(tenant),
            api_key=raw_key,
        )
