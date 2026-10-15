"""Unit tests for CORS settings helpers."""

from __future__ import annotations

import pytest

from app.core.config import Settings


def _settings(**overrides: object) -> Settings:
    """Build Settings with required secrets; overrides win."""
    base = {
        "postgres_user": "u",
        "postgres_password": "p",
        "postgres_db": "d",
        "api_key_pepper": "x" * 48,
        "debug": False,
        "cors_origins": [],
        "cors_allow_credentials": True,
    }
    base.update(overrides)
    return Settings(**base)  # type: ignore[arg-type]


@pytest.mark.unit
class TestEffectiveCorsOrigins:
    def test_debug_true_allows_all(self):
        s = _settings(debug=True, cors_origins=["https://app.example.com"])
        assert s.effective_cors_origins == ["*"]

    def test_debug_false_uses_configured_list(self):
        origins = ["https://panel.example.com", "http://localhost:3000"]
        s = _settings(debug=False, cors_origins=origins)
        assert s.effective_cors_origins == origins

    def test_debug_false_empty_list(self):
        s = _settings(debug=False, cors_origins=[])
        assert s.effective_cors_origins == []


@pytest.mark.unit
class TestEffectiveCorsAllowCredentials:
    def test_forced_false_when_debug(self):
        s = _settings(debug=True, cors_allow_credentials=True)
        assert s.effective_cors_allow_credentials is False

    def test_forced_false_when_wildcard_in_origins(self):
        s = _settings(debug=False, cors_origins=["*"], cors_allow_credentials=True)
        assert s.effective_cors_allow_credentials is False

    def test_true_when_explicit_origins(self):
        s = _settings(
            debug=False,
            cors_origins=["https://panel.example.com"],
            cors_allow_credentials=True,
        )
        assert s.effective_cors_allow_credentials is True

    def test_respects_false_when_explicit_origins(self):
        s = _settings(
            debug=False,
            cors_origins=["https://panel.example.com"],
            cors_allow_credentials=False,
        )
        assert s.effective_cors_allow_credentials is False

    def test_forced_false_when_origins_empty(self):
        # Empty allow list → no browser CORS; credentials irrelevant but safe
        s = _settings(debug=False, cors_origins=[], cors_allow_credentials=True)
        assert s.effective_cors_allow_credentials is False
