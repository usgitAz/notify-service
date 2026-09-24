"""
Domain-level exceptions.

These are framework-agnostic on purpose: the service layer can raise them
without importing FastAPI. Mapping to HTTP happens exclusively in the
API layer (exception_handlers.py).
"""

from __future__ import annotations

from app.schemas.common import ErrorDetail


class AppBaseException(Exception):
    """
    Base class for all domain exceptions.

    Attributes:
        code: Stable machine-readable error code.
        message: Human-readable message (safe to expose to clients).
        status_code: HTTP status to return when this reaches the API layer.
        details: Optional structured context, e.g. field-level validation errors.
    """

    default_code: str = "APP_ERROR"
    default_status_code: int = 400
    default_message: str = "An application error occurred."

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        status_code: int | None = None,
        details: list[ErrorDetail] | None = None,
    ) -> None:
        self.code = code or self.default_code
        self.message = message or self.default_message
        self.status_code = status_code or self.default_status_code
        self.details = details
        super().__init__(self.message)


# 4xx: Client errors


class ValidationError(AppBaseException):
    """Raised when input fails domain-level validation (not Pydantic)."""

    default_code = "VALIDATION_ERROR"
    default_status_code = 422
    default_message = "Request validation failed."


class AuthenticationError(AppBaseException):
    """Raised when credentials are missing or invalid."""

    default_code = "AUTHENTICATION_REQUIRED"
    default_status_code = 401
    default_message = "Authentication is required."


class AuthorizationError(AppBaseException):
    """Raised when the authenticated principal lacks permission."""

    default_code = "FORBIDDEN"
    default_status_code = 403
    default_message = "You do not have permission to perform this action."


class NotFoundError(AppBaseException):
    """Raised when a requested resource does not exist."""

    default_code = "NOT_FOUND"
    default_status_code = 404
    default_message = "Resource not found."


class ConflictError(AppBaseException):
    """Raised on unique-constraint violations or concurrent modifications."""

    default_code = "CONFLICT"
    default_status_code = 409
    default_message = "Resource already exists or conflicts with current state."


class RateLimitError(AppBaseException):
    """Raised when the caller exceeds the allowed request rate."""

    default_code = "RATE_LIMIT_EXCEEDED"
    default_status_code = 429
    default_message = "Too many requests. Please slow down."


# 5xx: Server / upstream errors


class ExternalServiceError(AppBaseException):
    """Raised when a downstream provider (FCM, SMTP, SMS gateway) fails."""

    default_code = "EXTERNAL_SERVICE_ERROR"
    default_status_code = 502
    default_message = "An upstream service failed."


class ServiceUnavailableError(AppBaseException):
    """Raised when the service itself is temporarily unable to handle traffic."""

    default_code = "SERVICE_UNAVAILABLE"
    default_status_code = 503
    default_message = "Service is temporarily unavailable."
