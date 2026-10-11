"""Health check response schemas."""

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    """Liveness probe response."""

    model_config = ConfigDict(json_schema_extra={"example": {"status": "healthy"}})

    status: str = Field(
        ...,
        description="Always 'healthy' when the process is alive.",
        examples=["healthy"],
    )


class HealthReadyChecks(BaseModel):
    """Individual dependency checks for readiness."""

    model_config = ConfigDict(
        frozen=True, json_schema_extra={"example": {"database": "ok", "redis": "ok"}}
    )

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


class HealthReadyResponse(BaseModel):
    """Readiness probe response."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "ready",
                "checks": {"database": "ok", "redis": "ok"},
            }
        }
    )

    status: str = Field(
        ...,
        description="'ready' if all checks pass, otherwise 'not ready'.",
        examples=["ready", "not ready"],
    )
    checks: HealthReadyChecks
