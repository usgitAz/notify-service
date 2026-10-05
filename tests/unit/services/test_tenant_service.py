"""Unit tests for TenantService."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.exceptions import ConflictError
from app.schemas.tenant import TenantCreate
from app.services.tenant_service import TenantService


@pytest.fixture
def service() -> TenantService:
    return TenantService()


def _fake_add(tenant_id=None):
    """Return a fake_add callable that populates server-default fields."""

    async def _add(session, tenant):
        tenant.id = tenant_id or uuid4()
        tenant.is_active = True
        tenant.created_at = datetime.now(UTC)
        tenant.updated_at = datetime.now(UTC)
        return tenant

    return _add


@pytest.mark.unit
class TestTenantServiceRegister:
    async def test_register_happy(self, service, monkeypatch):
        monkeypatch.setattr(service.repo, "get_by_name", AsyncMock(return_value=None))
        monkeypatch.setattr(service.repo, "add", AsyncMock(side_effect=_fake_add()))
        session = AsyncMock()

        result = await service.register(
            session,
            TenantCreate(name="Shop"),
            environment="test",
        )
        assert result.tenant.name == "Shop"
        assert result.api_key.startswith("sk_test_")

    async def test_duplicate_name(self, service, monkeypatch):
        monkeypatch.setattr(
            service.repo, "get_by_name", AsyncMock(return_value=MagicMock())
        )
        session = AsyncMock()
        with pytest.raises(ConflictError) as exc_info:
            await service.register(session, TenantCreate(name="Shop"))
        assert exc_info.value.code == "TENANT_NAME_TAKEN"

    async def test_register_live_env(self, service, monkeypatch):
        monkeypatch.setattr(service.repo, "get_by_name", AsyncMock(return_value=None))
        monkeypatch.setattr(service.repo, "add", AsyncMock(side_effect=_fake_add()))
        session = AsyncMock()

        result = await service.register(
            session, TenantCreate(name="Shop"), environment="live"
        )
        assert result.api_key.startswith("sk_live_")
