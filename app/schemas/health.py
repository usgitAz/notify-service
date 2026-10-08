"""Health check response schemas."""

from pydantic import Field

from app.schemas.base import BaseResponse


class HealthResponse(BaseResponse):
    """Liveness probe response."""

    status: str = Field(
        ...,
        description="Always 'healthy' when the process is alive.",
        examples=["healthy"],
    )


class HealthReadyChecks(BaseResponse):
    """Individual dependency checks for readiness."""

    database: str = Field(
        ...,
        description="'ok' when the DB responds, else 'error: <TypeName>'.",
        examples=["ok", "error: OperationalError"],
    )

    redis: str = Field(
        ...,
        description="'ok' when Redis responds, else 'error: <TypeName>'.",
        examples=["ok", "error: ConnectionError", "error: RedisNotConfigured"],
    )


class HealthReadyResponse(BaseResponse):
    """Readiness probe response."""

    status: str = Field(
        ...,
        description="'ready' if all checks pass, otherwise 'not ready'.",
        examples=["ready", "not ready"],
    )
    checks: HealthReadyChecks
