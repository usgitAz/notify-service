"""
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
    """A single field-level error."""

    model_config = ConfigDict(
        frozen=True,
        json_schema_extra={
            "example": {
                "field": "body.title",
                "code": "string_too_short",
                "message": "String should have at least 1 character",
            }
        },
    )

    field: str | None = Field(
        default=None, description="Dot-path to the offending field."
    )
    code: str | None = Field(default=None, description="Machine-readable sub-code.")
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


class ValidationErrorDetail(BaseModel):
    """Single field-level validation error."""

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

    field: str | None = Field(default=None)
    code: str | None = Field(default=None)
    message: str = Field(description="Human-readable description.")


class ValidationErrorBody(BaseModel):
    """The `error` object of a ValidationErrorResponse."""

    model_config = ConfigDict(frozen=True)

    code: str = Field(
        default="VALIDATION_ERROR",
        description="Always 'VALIDATION_ERROR' for 422 responses.",
        examples=["VALIDATION_ERROR"],
    )
    message: str = Field(
        default="Request data failed validation.",
        examples=["Request data failed validation."],
    )
    details: list[ValidationErrorDetail] = Field(
        description="List of field-level errors.",
    )


class ValidationErrorResponse(BaseModel):
    """Envelope for 422 validation errors."""

    model_config = ConfigDict(
        frozen=True,
        json_schema_extra={
            "example": {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request data failed validation.",
                    "details": [
                        {
                            "field": "body.external_id",
                            "code": "string_too_short",
                            "message": "String should have at least 1 character",
                        }
                    ],
                },
                "meta": {
                    "timestamp": "2026-10-11T12:00:00Z",
                    "request_id": "f0468f6b-cd9f-46bb-b87d-3cefdc1c0be6",
                },
            }
        },
    )

    success: bool = Field(default=False, frozen=True)
    error: ValidationErrorBody
    meta: ResponseMeta
