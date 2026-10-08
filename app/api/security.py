"""OpenAPI security schemes."""

from fastapi.security import APIKeyHeader

# Tenant API key sent via the X-API-Key header.
#
# `auto_error=False` — FastAPI will pass `None` if the header is missing,
# allowing us to raise our own AuthenticationError (with the project's
# consistent error envelope) instead of FastAPI's default 403.
api_key_header = APIKeyHeader(
    name="X-API-Key",
    scheme_name="APIKeyHeader",
    description="Tenant API key. Format: `sk_<env>_<random>`.",
    auto_error=False,
)
