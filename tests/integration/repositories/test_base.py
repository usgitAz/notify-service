"""Integration tests for BaseRepository."""

import pytest

from app.infrastructure.db.models import Tenant
from app.repositories.tenant_repo import TenantRepository


@pytest.mark.integration
class TestBaseRepository:
    async def test_get(self, db_session, tenant):
        repo = TenantRepository()
        result = await repo.get(db_session, tenant.id)
        assert result is not None
        assert result.id == tenant.id

    async def test_get_missing(self, db_session):
        from uuid import uuid4

        repo = TenantRepository()
        result = await repo.get(db_session, uuid4())
        assert result is None

    async def test_add(self, db_session):
        from app.core.security import (
            extract_prefix,
            generate_api_key,
            hash_api_key,
        )

        repo = TenantRepository()
        raw = generate_api_key("test")
        t = Tenant(
            name="added",
            api_key_hash=hash_api_key(raw),
            api_key_prefix=extract_prefix(raw),
        )
        result = await repo.add(db_session, t)
        assert result.id is not None
        assert result.created_at is not None

    async def test_delete(self, db_session, tenant):
        repo = TenantRepository()
        await repo.delete(db_session, tenant)
        await db_session.flush()
        result = await repo.get(db_session, tenant.id)
        assert result is None
