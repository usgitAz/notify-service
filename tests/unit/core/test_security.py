"""Unit tests for app.core.security."""

import pytest

from app.core.security import (
    extract_prefix,
    generate_api_key,
    hash_api_key,
    verify_api_key,
)


@pytest.mark.unit
class TestGenerateApiKey:
    def test_live_format(self):
        key = generate_api_key("live")
        assert key.startswith("sk_live_")
        assert len(key) > 30

    def test_test_format(self):
        key = generate_api_key("test")
        assert key.startswith("sk_test_")

    def test_default_environment_is_live(self):
        assert generate_api_key().startswith("sk_live_")

    def test_uniqueness(self):
        keys = {generate_api_key("live") for _ in range(200)}
        assert len(keys) == 200


@pytest.mark.unit
class TestHashApiKey:
    def test_deterministic(self):
        assert hash_api_key("abc") == hash_api_key("abc")

    def test_sha256_length(self):
        assert len(hash_api_key("anything")) == 64

    def test_different_inputs_different_hashes(self):
        assert hash_api_key("a") != hash_api_key("b")


@pytest.mark.unit
class TestVerifyApiKey:
    def test_correct_key(self):
        key = generate_api_key("live")
        assert verify_api_key(key, hash_api_key(key)) is True

    def test_wrong_key(self):
        key = generate_api_key("live")
        assert verify_api_key("wrong", hash_api_key(key)) is False

    def test_case_sensitive(self):
        key = "sk_live_ABC"
        assert verify_api_key("sk_live_abc", hash_api_key(key)) is False


@pytest.mark.unit
class TestExtractPrefix:
    def test_full_key(self):
        key = "sk_live_ABCDEFGHIJKLMNOP"
        assert extract_prefix(key) == "sk_live_ABCDEFGH"

    def test_test_env(self):
        key = "sk_test_abcdefghijklmnop"
        assert extract_prefix(key) == "sk_test_abcdefgh"

    def test_short_key_fallback(self):
        assert extract_prefix("short") == "short"
