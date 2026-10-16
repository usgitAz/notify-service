"""Integration tests for UserRepository."""

import pytest

from app.infrastructure.db.models import User
from app.repositories.user_repo import UserRepository


@pytest.mark.integration
class TestListByTenant:
    async def test_empty(self, db_session, tenant):
        repo = UserRepository()
        items, total = await repo.list_by_tenant(db_session, tenant.id)
        assert items == []
        assert total == 0

    async def test_returns_users(self, db_session, tenant, user):
        repo = UserRepository()
        items, total = await repo.list_by_tenant(db_session, tenant.id)
        assert total == 1
        assert items[0].id == user.id

    async def test_returns_active_and_inactive_by_default(self, db_session, tenant):
        repo = UserRepository()
        active = User(tenant_id=tenant.id, external_id="active", email="a@x.com")
        inactive = User(
            tenant_id=tenant.id,
            external_id="inactive",
            email="i@x.com",
            is_active=False,
        )
        db_session.add_all([active, inactive])
        await db_session.flush()

        items, total = await repo.list_by_tenant(db_session, tenant.id)
        assert total == 2
        assert {u.external_id for u in items} == {"active", "inactive"}

    async def test_filter_active_only(self, db_session, tenant):
        repo = UserRepository()
        active = User(tenant_id=tenant.id, external_id="active", email="a@x.com")
        inactive = User(
            tenant_id=tenant.id,
            external_id="inactive",
            email="i@x.com",
            is_active=False,
        )
        db_session.add_all([active, inactive])
        await db_session.flush()

        items, total = await repo.list_by_tenant(db_session, tenant.id, is_active=True)
        assert total == 1
        assert items[0].external_id == "active"

    async def test_filter_inactive_only(self, db_session, tenant):
        repo = UserRepository()
        active = User(tenant_id=tenant.id, external_id="active", email="a@x.com")
        inactive = User(
            tenant_id=tenant.id,
            external_id="inactive",
            email="i@x.com",
            is_active=False,
        )
        db_session.add_all([active, inactive])
        await db_session.flush()

        items, total = await repo.list_by_tenant(db_session, tenant.id, is_active=False)
        assert total == 1
        assert items[0].external_id == "inactive"
