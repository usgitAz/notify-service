"""
API Key generation and verification.

Format:    sk_<env>_<random>  (env = "live" | "test")
Storage:   HMAC-SHA256 with server-side pepper (never in DB).
Verify:    constant-time comparison to prevent timing attacks.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import Literal

from app.core.config import settings

# Constants
API_KEY_PREFIX = "sk"
API_KEY_BYTES = 32
API_KEY_RANDOM_DISPLAY_LENGTH = 8


def generate_api_key(environment: Literal["live", "test"] = "live") -> str:
    """Generate a new API key: sk_<env>_<random>."""
    random_part = secrets.token_urlsafe(API_KEY_BYTES)
    return f"{API_KEY_PREFIX}_{environment}_{random_part}"


def hash_api_key(api_key: str) -> str:
    """Hash an API key with HMAC-SHA256 + server pepper."""
    return hmac.new(
        key=settings.api_key_pepper.encode("utf-8"),
        msg=api_key.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()


def verify_api_key(plain_key: str, stored_hash: str) -> bool:
    """Constant-time verification of an API key against its stored hash."""
    computed = hash_api_key(plain_key)
    return hmac.compare_digest(computed, stored_hash)


def extract_prefix(api_key: str) -> str:
    """
    Extract a short prefix for display: sk_<env>_<8 chars>.

    Example:
        sk_live_Xy9kL2mN... → sk_live_Xy9k7aON
        sk_test_Abc3XyZ7... → sk_test_Abc3u2Af
    """
    parts = api_key.split("_")
    if len(parts) < 3:
        return api_key[:12]
    return f"{parts[0]}_{parts[1]}_{parts[2][:API_KEY_RANDOM_DISPLAY_LENGTH]}"
