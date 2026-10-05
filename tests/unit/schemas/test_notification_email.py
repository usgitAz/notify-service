"""Unit tests for NotificationEmailCreate schema."""

import pytest
from pydantic import ValidationError

from app.schemas.notification import NotificationEmailCreate


@pytest.mark.unit
class TestNotificationEmailCreateValid:
    def test_minimal(self):
        n = NotificationEmailCreate(
            user_id="user-1",
            subject="Hi",
            body="Hello",
        )
        assert n.user_id == "user-1"
        assert n.cc is None
        assert n.bcc is None
        assert n.attachments is None

    def test_full(self):
        n = NotificationEmailCreate(
            user_id="user-1",
            subject="Hi",
            body="Hello",
            from_email="noreply@x.com",
            reply_to="support@x.com",
            cc=["a@x.com"],
            bcc=["b@x.com"],
            attachments=["https://x.com/a.pdf"],
        )
        assert n.from_email == "noreply@x.com"
        assert n.cc == ["a@x.com"]


@pytest.mark.unit
class TestNotificationEmailCreateValidation:
    def test_missing_user_id(self):
        with pytest.raises(ValidationError):
            NotificationEmailCreate(subject="Hi", body="Hello")

    def test_missing_subject(self):
        with pytest.raises(ValidationError):
            NotificationEmailCreate(user_id="u", body="Hello")

    def test_empty_body(self):
        with pytest.raises(ValidationError):
            NotificationEmailCreate(user_id="u", subject="Hi", body="")

    def test_empty_subject(self):
        with pytest.raises(ValidationError):
            NotificationEmailCreate(user_id="u", subject="", body="Hello")

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            NotificationEmailCreate(
                user_id="u",
                subject="Hi",
                body="Hello",
                from_email="not-an-email",
            )

    def test_unknown_field_rejected(self):
        with pytest.raises(ValidationError):
            NotificationEmailCreate(
                user_id="u",
                subject="Hi",
                body="Hello",
                unknown_field="x",  # type: ignore[call-arg]
            )


@pytest.mark.unit
class TestDedupeValidator:
    def test_cc_dedup(self):
        n = NotificationEmailCreate(
            user_id="u",
            subject="Hi",
            body="Hello",
            cc=["a@x.com", "a@x.com", "b@x.com"],
        )
        assert n.cc == ["a@x.com", "b@x.com"]

    def test_bcc_dedup(self):
        n = NotificationEmailCreate(
            user_id="u",
            subject="Hi",
            body="Hello",
            bcc=["x@x.com", "x@x.com"],
        )
        assert n.bcc == ["x@x.com"]

    def test_attachments_dedup(self):
        n = NotificationEmailCreate(
            user_id="u",
            subject="Hi",
            body="Hello",
            attachments=["a", "b", "a"],
        )
        assert n.attachments == ["a", "b"]

    def test_empty_list_becomes_none(self):
        n = NotificationEmailCreate(
            user_id="u",
            subject="Hi",
            body="Hello",
            cc=[],
        )
        assert n.cc is None
