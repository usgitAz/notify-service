"""
Common response schemas used across the entire API.

Design principles:
- Two envelopes: SuccessResponse[T] and ErrorResponse.
- Every response carries `meta` with a request_id for tracing.
- Error shape is stable and machine-readable (code) + human-readable (message).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


def _utc_now() -> datetime:
    """Return timezone-aware UTC now. Never use native datetimes."""
    return datetime.now(UTC)


class ResponseMeta(BaseModel):
    """Metadata attached to every API response."""

    model_config = ConfigDict(frozen=True)

    timestamp: datetime = Field(default_factory=_utc_now)
    request_id: str | None = Field(
        default=None,
        description="Correlation ID. Echo of X-Request-ID header.",
    )


class ErrorDetail(BaseModel):
    """
    A single field-level error.

    Used mainly for validation errors, where multiple fields
    may fail at once.
    """

    model_config = ConfigDict(frozen=True)

    field: str | None = Field(
        default=None,
        description="Dot-path to the offending field, e.g. 'channel.token'.",
    )
    code: str | None = Field(
        default=None,
        description="Machine-readable sub-code, e.g. 'string_too_short'.",
    )
    message: str = Field(description="Human-readable description of the problem.")


class ErrorBody(BaseModel):
    """The `error` object of an ErrorResponse."""

    model_config = ConfigDict(frozen=True)

    code: str = Field(
        description="Stable, machine-readable error code (SCREAMING_SNAKE_CASE).",
        examples=["NOTIFICATION_NOT_FOUND", "VALIDATION_ERROR"],
    )
    message: str = Field(
        description="Human-readable message. May change over time; do not branch on it.",
        examples=["Notification with id 'abc' was not found."],
    )
    details: list[ErrorDetail] | None = Field(
        default=None,
        description="Additional, structured context. Typically validation errors.",
    )


class SuccessResponse[T](BaseModel):
    """Envelope for successful responses."""

    model_config = ConfigDict(frozen=True)

    success: bool = Field(default=True, frozen=True)
    data: T
    meta: ResponseMeta


class ErrorResponse(BaseModel):
    """Envelope for error responses. Also used as OpenAPI documentation model."""

    model_config = ConfigDict(frozen=True)

    success: bool = Field(default=False, frozen=True)
    error: ErrorBody
    meta: ResponseMeta
