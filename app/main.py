from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import logging_lifespan

app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=logging_lifespan,
)

# import routers
from app.api.v1.endpoints import health

app.include_router(health.router)
