"""
Errors raised by external clients (SMTP, FCM, ...).

Two categories:
- PermanentError: retrying won't help (bad recipient, auth fail).
- TransientError: retrying MIGHT help (timeout, network).
"""

from __future__ import annotations


class ClientError(Exception):
    """Base class for all external client errors."""

    def __init__(self, message: str, *, reason: str | None = None) -> None:
        self.reason = reason
        super().__init__(message)


class PermanentError(ClientError):
    """
    Error that will NOT succeed on retry.

    Examples:
    - Invalid email address (rejected by SMTP).
    - Revoked push token.
    - Authentication failure.

    Handling: mark notification as `failed`, no retries.
    """


class TransientError(ClientError):
    """
    Error that might succeed on retry.

    Examples:
    - Network timeout.
    - Temporary SMTP/FCM outage.
    - Rate limit (after a delay).

    Handling: retry up to MAX_ATTEMPTS with backoff.
    """
