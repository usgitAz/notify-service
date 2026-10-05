"""Test __repr__ methods for all models."""

import pytest

from app.infrastructure.db.models import (
    Device,
    DevicePlatform,
    Notification,
    NotificationChannel,
    NotificationStatus,
    PushProvider,
    Tenant,
    User,
)


@pytest.mark.unit
class TestRepr:
    def test_tenant_repr(self):
        t = Tenant(name="x")
        t.id = "abc"
        t.is_active = True
        s = repr(t)
        assert "Tenant" in s
        assert "x" in s

    def test_user_repr(self):
        u = User(tenant_id="t", external_id="ali")
        u.id = "u-1"
        u.is_active = True
        s = repr(u)
        assert "User" in s
        assert "ali" in s

    def test_device_repr(self):
        d = Device(
            user_id="u",
            platform=DevicePlatform.IOS,
            provider=PushProvider.FCM,
            token="x",
        )
        d.id = "d-1"
        d.is_active = True
        s = repr(d)
        assert "Device" in s
        assert "ios" in s

    def test_notification_repr(self):
        n = Notification(
            tenant_id="t",
            user_id="u",
            channel=NotificationChannel.EMAIL,
            title="x",
            body="y",
        )
        n.id = "n-1"
        n.status = NotificationStatus.PENDING
        n.attempts = 0
        s = repr(n)
        assert "Notification" in s
        assert "email" in s
