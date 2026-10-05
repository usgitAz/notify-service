"""Unit-test-specific fixtures.

These fixtures create model instances WITHOUT a DB session.
They are used by service tests where repos are mocked.
"""

from uuid import uuid4

import pytest

from app.infrastructure.db.models import Tenant, User


@pytest.fixture
def fake_tenant() -> Tenant:
    """A Tenant instance with a populated id, without touching the DB."""
    t = Tenant(name="fake-tenant")
    t.id = uuid4()
    return t


@pytest.fixture
def fake_user(fake_tenant: Tenant) -> User:
    """A User instance with a populated id, without touching the DB."""
    u = User(tenant_id=fake_tenant.id, external_id="fake-user")
    u.id = uuid4()
    return u
