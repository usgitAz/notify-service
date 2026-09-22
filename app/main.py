from fastapi import FastAPI

from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
)

# import routers
from app.api.v1.endpoints import health

app.include_router(health.router)
