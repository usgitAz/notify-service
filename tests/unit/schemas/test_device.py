"""Unit tests for Device schemas."""

import pytest
from pydantic import ValidationError

from app.infrastructure.db.models import DevicePlatform, PushProvider
from app.schemas.device import DeviceCreate, DeviceUpdate


@pytest.mark.unit
class TestDeviceCreate:
    def test_minimal(self):
        d = DeviceCreate(platform=DevicePlatform.IOS, token="tok-1")
        assert d.platform == DevicePlatform.IOS
        assert d.provider == PushProvider.FCM  # default
        assert d.device_name is None

    def test_full(self):
        d = DeviceCreate(
            platform=DevicePlatform.ANDROID,
            provider=PushProvider.FCM,
            token="tok",
            device_name="Pixel 8",
        )
        assert d.device_name == "Pixel 8"

    def test_missing_token(self):
        with pytest.raises(ValidationError):
            DeviceCreate(platform=DevicePlatform.IOS)  # type: ignore[call-arg]

    def test_empty_token(self):
        with pytest.raises(ValidationError):
            DeviceCreate(platform=DevicePlatform.IOS, token="")

    def test_device_name_too_long(self):
        with pytest.raises(ValidationError):
            DeviceCreate(
                platform=DevicePlatform.IOS,
                token="tok",
                device_name="x" * 101,
            )

    def test_invalid_platform(self):
        with pytest.raises(ValidationError):
            DeviceCreate(platform="apple", token="tok")  # type: ignore[arg-type]


@pytest.mark.unit
class TestDeviceUpdate:
    def test_all_none(self):
        d = DeviceUpdate()
        assert d.device_name is None
        assert d.is_active is None

    def test_device_name(self):
        d = DeviceUpdate(device_name="New")
        assert d.device_name == "New"

    def test_deactivate(self):
        d = DeviceUpdate(is_active=False)
        assert d.is_active is False
