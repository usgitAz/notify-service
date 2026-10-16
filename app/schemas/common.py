"""
Common response schemas used across the entire API.

Design:
- One success envelope: `SuccessResponse[T]`.
- One error envelope: `ErrorResponse`. Validation errors (422) are
  just an `ErrorResponse` with a populated `details[]` list — no
  separate schema needed.
- Every response carries `meta` with a request_id for tracing.
- Error shape is stable and machine-readable (code) + human-readable (message).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TypeVar

from pydantic import BaseModel, ConfigDict, Field, computed_field

T = TypeVar("T")


def _utc_now() -> datetime:
    """Return timezone-aware UTC now. Never use native datetimes."""
    return datetime.now(UTC)


class ResponseMeta(BaseModel):
    """Metadata attached to every API response."""

    model_config = ConfigDict(
        frozen=True,
        json_schema_extra={
            "example": {
                "timestamp": "2026-10-11T12:00:00Z",
                "request_id": "f0468f6b-cd9f-46bb-b87d-3cefdc1c0be6",
            }
        },
    )

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

    model_config = ConfigDict(
        frozen=True,
        json_schema_extra={
            "example": {
                "field": "body.external_id",
                "code": "string_too_short",
                "message": "String should have at least 1 character",
            }
        },
    )

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

    model_config = ConfigDict(
        frozen=True,
        json_schema_extra={
            "example": {
                "code": "USER_NOT_FOUND",
                "message": "User 'alice' not found.",
                "details": None,
            }
        },
    )

    code: str = Field(
        description="Stable, machine-readable error code (SCREAMING_SNAKE_CASE).",
        examples=["USER_NOT_FOUND", "VALIDATION_ERROR"],
    )
    message: str = Field(
        description="Human-readable message. May change over time; do not branch on it.",
        examples=["User 'alice' not found."],
    )
    details: list[ErrorDetail] | None = Field(
        default=None,
        description=("Additional, structured context. "),
    )


class ErrorResponse(BaseModel):
    """Envelope for error responses. Also used as OpenAPI documentation model."""

    model_config = ConfigDict(
        frozen=True,
        json_schema_extra={
            "example": {
                "success": False,
                "error": {
                    "code": "USER_NOT_FOUND",
                    "message": "User 'alice' not found.",
                    "details": None,
                },
                "meta": {
                    "timestamp": "2026-10-11T12:00:00Z",
                    "request_id": "f0468f6b-cd9f-46bb-b87d-3cefdc1c0be6",
                },
            }
        },
    )

    success: bool = Field(default=False, frozen=True)
    error: ErrorBody
    meta: ResponseMeta


class SuccessResponse[T](BaseModel):
    """Envelope for successful responses."""

    model_config = ConfigDict(frozen=True)

    success: bool = Field(default=True, frozen=True)
    data: T
    meta: ResponseMeta


class Page[T](BaseModel):
    """
    Paginated list payload for all list endpoints.

    Used as SuccessResponse.data so the outer envelope stays identical.
    """

    model_config = ConfigDict(frozen=True)

    items: list[T]
    total: int = Field(ge=0, description="Total rows matching filters (before page).")
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def has_next(self) -> bool:
        return self.offset + self.limit < self.total

    @computed_field  # type: ignore[prop-decorator]
    @property
    def has_prev(self) -> bool:
        return self.offset > 0
