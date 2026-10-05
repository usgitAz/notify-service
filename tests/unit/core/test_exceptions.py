"""Unit tests for app.core.exceptions."""

import pytest

from app.core.exceptions import (
    AppBaseException,
    AuthenticationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)


@pytest.mark.unit
class TestExceptionDefaults:
    def test_base_defaults(self):
        exc = AppBaseException()
        assert exc.status_code == 400
        assert exc.code == "APP_ERROR"
        assert "application error" in exc.message.lower()

    def test_custom_message(self):
        exc = ValidationError("Custom message")
        assert exc.message == "Custom message"
        assert exc.code == "VALIDATION_ERROR"

    def test_custom_code(self):
        exc = NotFoundError("Not here", code="USER_NOT_FOUND")
        assert exc.code == "USER_NOT_FOUND"
        assert exc.status_code == 404

    def test_str_returns_message(self):
        exc = ConflictError("Already exists")
        assert str(exc) == "Already exists"


@pytest.mark.unit
@pytest.mark.parametrize(
    ("exc_class", "expected_code", "expected_status"),
    [
        (ValidationError, "VALIDATION_ERROR", 422),
        (AuthenticationError, "AUTHENTICATION_REQUIRED", 401),
        (NotFoundError, "NOT_FOUND", 404),
        (ConflictError, "CONFLICT", 409),
    ],
)
def test_subclass_defaults(exc_class, expected_code, expected_status):
    exc = exc_class()
    assert exc.code == expected_code
    assert exc.status_code == expected_status
