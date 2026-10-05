"""Integration tests for TenantRepository."""

import pytest

from app.repositories.tenant_repo import TenantRepository


@pytest.mark.integration
class TestGetByName:
    async def test_finds_active(self, db_session, tenant):
        repo = TenantRepository()
        result = await repo.get_by_name(db_session, tenant.name)
        assert result is not None
        assert result.id == tenant.id

    async def test_skips_inactive(self, db_session, tenant):
        repo = TenantRepository()
        tenant.is_active = False
        await db_session.flush()
        result = await repo.get_by_name(db_session, tenant.name)
        assert result is None

    async def test_not_found(self, db_session):
        repo = TenantRepository()
        result = await repo.get_by_name(db_session, "nope")
        assert result is None


@pytest.mark.integration
class TestGetByApiKeyPrefix:
    async def test_finds(self, db_session, tenant):
        repo = TenantRepository()
        result = await repo.get_by_api_key_prefix(db_session, tenant.api_key_prefix)
        assert result is not None
        assert result.id == tenant.id

    async def test_inactive_not_found(self, db_session, tenant):
        repo = TenantRepository()
        tenant.is_active = False
        await db_session.flush()
        result = await repo.get_by_api_key_prefix(db_session, tenant.api_key_prefix)
        assert result is None

    async def test_not_found(self, db_session):
        repo = TenantRepository()
        result = await repo.get_by_api_key_prefix(db_session, "sk_test_nope")
        assert result is None
