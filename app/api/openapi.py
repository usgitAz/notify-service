from typing import Any

from app.schemas.common import ErrorResponse, ValidationErrorResponse
from app.schemas.health import HealthReadyResponse

# Cosmetic values used only in Swagger examples
_TS = "2026-10-09T17:13:13.011Z"
_RID = "f0468f6b-cd9f-46bb-b87d-3cefdc1c0be6"


# Core factory


def error_response(
    status_code: int,
    *,
    code: str,
    message: str,
    description: str | None = None,
) -> dict[int | str, dict[str, Any]]:
    """
    Build a single OpenAPI error response entry.
    """
    return {
        status_code: {
            "model": ErrorResponse,
            "description": description or message,
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": code,
                            "message": message,
                            "details": None,
                        },
                        "meta": {
                            "timestamp": _TS,
                            "request_id": _RID,
                        },
                    }
                }
            },
        }
    }


def responses(
    *items: dict[int | str, dict[str, Any]],
) -> dict[int | str, dict[str, Any]]:
    """
    Merge several error_response(...) results into one dict.
    """
    merged: dict[int | str, dict[str, Any]] = {}
    for item in items:
        merged.update(item)
    return merged


# Specialized responses


def validation_response(
    *,
    description: str = "Request validation failed.",
) -> dict[int | str, dict[str, Any]]:
    return {
        422: {
            "model": ValidationErrorResponse,
            "description": description,
            "content": {
                "application/json": {
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
                            "timestamp": _TS,
                            "request_id": _RID,
                        },
                    }
                }
            },
        }
    }


def ready_unavailable_response() -> dict[int | str, dict[str, Any]]:
    return {
        503: {
            "model": HealthReadyResponse,
            "description": "One or more dependencies are unavailable.",
            "content": {
                "application/json": {
                    "example": {
                        "status": "not ready",
                        "checks": {
                            "database": "ok",
                            "redis": "error: ConnectionError",
                        },
                    }
                }
            },
        }
    }


# Router-level defaults

RESPONSES_401: dict[int | str, dict[str, Any]] = error_response(
    401,
    code="AUTHENTICATION_REQUIRED",
    message="Invalid or missing API key.",
)

RESPONSES_500: dict[int | str, dict[str, Any]] = error_response(
    500,
    code="INTERNAL_SERVER_ERROR",
    message="An unexpected error occurred. Please try again later.",
)

RESPONSES_422: dict[int | str, dict[str, Any]] = validation_response()

RESPONSES_AUTHENTICATED: dict[int | str, dict[str, Any]] = {
    **RESPONSES_401,
    **RESPONSES_422,
    **RESPONSES_500,
}

RESPONSES_PUBLIC: dict[int | str, dict[str, Any]] = {
    **RESPONSES_500,
}

RESPONSES_UNAVAILABLE: dict[int | str, dict[str, Any]] = ready_unavailable_response()

# openapi tags
tags_metadata = [
    {"name": "health", "description": "Liveness and readiness probes for monitoring."},
    {
        "name": "users",
        "description": "Manage end-users of a tenant, identified by external_id.",
    },
    {
        "name": "devices",
        "description": "Register and manage push devices. Tokens must be globally unique.",
    },
    {
        "name": "notifications",
        "description": "Create, list, and inspect notifications. Delivery is asynchronous.",
    },
]
