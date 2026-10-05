"""Unit tests for User schemas."""

import pytest
from pydantic import ValidationError

from app.schemas.user import UserCreate, UserUpdate


@pytest.mark.unit
class TestUserCreate:
    def test_minimal(self):
        u = UserCreate(external_id="user-1")
        assert u.external_id == "user-1"
        assert u.email is None

    def test_with_email(self):
        u = UserCreate(external_id="user-1", email="a@b.com")
        assert u.email == "a@b.com"

    def test_missing_external_id(self):
        with pytest.raises(ValidationError):
            UserCreate()  # type: ignore[call-arg]

    def test_empty_external_id(self):
        with pytest.raises(ValidationError):
            UserCreate(external_id="")

    def test_external_id_too_long(self):
        with pytest.raises(ValidationError):
            UserCreate(external_id="x" * 256)

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            UserCreate(external_id="u", email="not-an-email")

    def test_unknown_field_rejected(self):
        with pytest.raises(ValidationError):
            UserCreate(external_id="u", unknown="x")  # type: ignore[call-arg]

    def test_whitespace_trimmed(self):
        u = UserCreate(external_id="  user-1  ")
        assert u.external_id == "user-1"


@pytest.mark.unit
class TestUserUpdate:
    def test_all_none(self):
        u = UserUpdate()
        assert u.email is None
        assert u.is_active is None

    def test_email_only(self):
        u = UserUpdate(email="new@x.com")
        assert u.email == "new@x.com"
        assert u.is_active is None

    def test_is_active_only(self):
        u = UserUpdate(is_active=False)
        assert u.email is None
        assert u.is_active is False

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            UserUpdate(email="bad")

    def test_unknown_field_rejected(self):
        with pytest.raises(ValidationError):
            UserUpdate(unknown="x")  # type: ignore[call-arg]
