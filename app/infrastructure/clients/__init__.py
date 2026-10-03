"""External clients package."""

from app.infrastructure.clients.email_client import email_client
from app.infrastructure.clients.exceptions import (
    ClientError,
    PermanentError,
    TransientError,
)

__all__ = [
    "email_client",
    "ClientError",
    "PermanentError",
    "TransientError",
]
