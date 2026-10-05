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

    async def test_filters_inactive(self, db_session, tenant):
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
        assert total == 1
        assert items[0].external_id == "active"

    async def test_pagination(self, db_session, tenant):
        repo = UserRepository()
        for i in range(5):
            db_session.add(User(tenant_id=tenant.id, external_id=f"u{i}"))
        await db_session.flush()

        items, total = await repo.list_by_tenant(db_session, tenant.id, limit=2)
        assert total == 5
        assert len(items) == 2
