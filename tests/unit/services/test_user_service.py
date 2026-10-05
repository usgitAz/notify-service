"""Unit tests for UserService (repos mocked)."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import ConflictError, NotFoundError
from app.infrastructure.db.models import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.user_service import UserService


@pytest.fixture
def service() -> UserService:
    return UserService()


@pytest.mark.unit
class TestUserServiceCreate:
    async def test_creates_user(self, service, fake_tenant, monkeypatch):
        monkeypatch.setattr(
            service.repo, "get_by_external_id_any", AsyncMock(return_value=None)
        )
        monkeypatch.setattr(
            service.repo,
            "add",
            AsyncMock(side_effect=lambda s, u: u),
        )
        session = AsyncMock()
        user = await service.create(
            session,
            fake_tenant,
            UserCreate(external_id="ali", email="ali@x.com"),
        )
        assert user.external_id == "ali"
        assert user.email == "ali@x.com"
        assert user.tenant_id == fake_tenant.id

    async def test_existing_active_raises_conflict(
        self, service, fake_tenant, monkeypatch
    ):
        existing = MagicMock()
        existing.is_active = True
        monkeypatch.setattr(
            service.repo, "get_by_external_id_any", AsyncMock(return_value=existing)
        )
        session = AsyncMock()
        with pytest.raises(ConflictError) as exc_info:
            await service.create(session, fake_tenant, UserCreate(external_id="ali"))
        assert exc_info.value.code == "USER_ALREADY_EXISTS"

    async def test_existing_inactive_raises_inactive_error(
        self, service, fake_tenant, monkeypatch
    ):
        existing = MagicMock()
        existing.is_active = False
        monkeypatch.setattr(
            service.repo, "get_by_external_id_any", AsyncMock(return_value=existing)
        )
        session = AsyncMock()
        with pytest.raises(ConflictError) as exc_info:
            await service.create(session, fake_tenant, UserCreate(external_id="ali"))
        assert exc_info.value.code == "USER_EXISTS_INACTIVE"


@pytest.mark.unit
class TestUserServiceGet:
    async def test_returns_user(self, service, fake_tenant, monkeypatch):
        user = User(tenant_id=fake_tenant.id, external_id="ali")
        monkeypatch.setattr(
            service.repo, "get_by_external_id", AsyncMock(return_value=user)
        )
        session = AsyncMock()
        result = await service.get_by_external_id(session, fake_tenant, "ali")
        assert result is user

    async def test_not_found(self, service, fake_tenant, monkeypatch):
        monkeypatch.setattr(
            service.repo, "get_by_external_id", AsyncMock(return_value=None)
        )
        session = AsyncMock()
        with pytest.raises(NotFoundError):
            await service.get_by_external_id(session, fake_tenant, "missing")


@pytest.mark.unit
class TestUserServiceUpdate:
    async def test_update_email(self, service, fake_tenant, monkeypatch):
        user = User(
            tenant_id=fake_tenant.id,
            external_id="ali",
            email="old@x.com",
        )
        user.is_active = True
        monkeypatch.setattr(
            service.repo, "get_by_external_id_any", AsyncMock(return_value=user)
        )
        session = AsyncMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        await service.update(session, fake_tenant, "ali", UserUpdate(email="new@x.com"))
        assert user.email == "new@x.com"

    async def test_soft_delete(self, service, fake_tenant, monkeypatch):
        user = User(tenant_id=fake_tenant.id, external_id="ali")
        user.is_active = True
        user.deactivated_at = None
        monkeypatch.setattr(
            service.repo, "get_by_external_id_any", AsyncMock(return_value=user)
        )
        session = AsyncMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        await service.update(session, fake_tenant, "ali", UserUpdate(is_active=False))
        assert user.is_active is False
        assert user.deactivated_at is not None

    async def test_reactivate(self, service, fake_tenant, monkeypatch):
        user = User(tenant_id=fake_tenant.id, external_id="ali")
        user.is_active = False
        monkeypatch.setattr(
            service.repo, "get_by_external_id_any", AsyncMock(return_value=user)
        )
        session = AsyncMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        await service.update(session, fake_tenant, "ali", UserUpdate(is_active=True))
        assert user.is_active is True
        assert user.deactivated_at is None

    async def test_update_no_changes(self, service, fake_tenant, monkeypatch):
        user = User(tenant_id=fake_tenant.id, external_id="ali", email="a@x.com")
        user.is_active = True
        monkeypatch.setattr(
            service.repo, "get_by_external_id_any", AsyncMock(return_value=user)
        )
        session = AsyncMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        # is_active same as current → no change
        await service.update(session, fake_tenant, "ali", UserUpdate(is_active=True))
        assert user.is_active is True

    async def test_not_found(self, service, fake_tenant, monkeypatch):
        monkeypatch.setattr(
            service.repo, "get_by_external_id_any", AsyncMock(return_value=None)
        )
        session = AsyncMock()
        with pytest.raises(NotFoundError):
            await service.update(
                session, fake_tenant, "missing", UserUpdate(email="x@y.com")
            )
