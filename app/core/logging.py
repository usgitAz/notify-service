# from typing import Literal

from fapilog import get_logger
from fapilog.fastapi import FastAPIBuilder

from app.core.config import settings

# Runtime enrichers are excluded to keep access logs lean.
# Only context_vars (request/correlation IDs) is kept.
logging_lifespan = (
    FastAPIBuilder()
    .with_preset("dev" if settings.debug else "production")
    .with_enrichers("context_vars")  # runtime_info (host, pid, python) deleted
    .sample_rate(settings.log_sample_rate)
    .skip_paths(settings.log_skip_paths)
    .build()
)

logger = get_logger(name="notify_service")
