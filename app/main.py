from fastapi import FastAPI

from app.api.exception_handlers import register_exception_handlers
from app.core.config import settings
from app.core.logging import logging_lifespan
from app.middleware.request_id import RequestIDMiddleware

app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=logging_lifespan,
)

# middlewares
app.add_middleware(RequestIDMiddleware)

register_exception_handlers(app)


# import routers
from app.api.v1.endpoints import health

app.include_router(health.router)
