"""Health check endpoints."""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RedisDep, get_db
from app.schemas.health import HealthReadyChecks, HealthReadyResponse, HealthResponse

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Liveness probe",
    description="Returns 200 if the process is alive.",
    response_model=HealthResponse,
)
async def health() -> HealthResponse:
    """Liveness — process is running. No dependencies checked."""
    return HealthResponse(status="healthy")


@router.get(
    "/health/ready",
    summary="Readiness probe",
    description=(
        "Returns 200 if the app is ready to serve traffic. "
        "Checks database and Redis connectivity."
    ),
    response_model=HealthReadyResponse,
    responses={
        503: {
            "model": HealthReadyResponse,
            "description": "One or more dependencies are unavailable.",
        },
    },
)
async def ready(
    response: Response,
    session: AsyncSession = Depends(get_db),
    redis: RedisDep = None,
) -> HealthReadyResponse:
    """Readiness — check all critical dependencies."""
    checks: dict[str, str] = {}

    # 1. Database
    try:
        await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {type(exc).__name__}"

    # 2. Redis
    if redis is None:
        checks["redis"] = "error: RedisNotConfigured"
    else:
        try:
            await redis.ping()
            checks["redis"] = "ok"
        except Exception as exc:
            checks["redis"] = f"error: {type(exc).__name__}"

    # Overall
    all_ok = all(v == "ok" for v in checks.values())
    if not all_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthReadyResponse(
        status="ready" if all_ok else "not ready",
        checks=HealthReadyChecks(
            database=checks["database"],
            redis=checks["redis"],
        ),
    )
