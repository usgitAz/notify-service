from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Liveness probe",
    description="Returns 200 if the process is alive",
)
async def health() -> dict:
    """Liveness - process is running. No dependecies checked."""
    return {"status": "healthy"}


@router.get(
    "/health/ready",
    summary="Readiness probe",
    description=(
        "Returns 200 if the app is ready to serve traffic. "
        "Checks database connectivity."
    ),
)
async def ready(response: Response, session: AsyncSession = Depends(get_db)) -> dict:
    """Readiness - check all critical dependencies."""
    checks: dict[str, str] = {}
    try:
        await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {type(exc).__name__}"

    all_ok = all(v == "ok" for v in checks.values())

    if not all_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {"status": "ready" if all_ok else "not ready", "checks": checks}
