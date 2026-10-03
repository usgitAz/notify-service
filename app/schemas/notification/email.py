"""
The shared fields (`user_id`, `title`, `body`) are explicit.
Email-specific fields (`from_email`, `reply_to`, `cc`, `bcc`,
`attachments`) live in the request but are stored in `payload` (JSONB).
"""

from __future__ import annotations

from pydantic import EmailStr, Field, field_validator

from app.schemas.base import BaseRequest


class NotificationEmailCreate(BaseRequest):
    """
    Targeting:
    - `user_id` must be an active user of the authenticated tenant.
    - The user must have an `email` set (else 422).

    Email-specific fields are optional and stored in `payload`:
    - `from_email`   → custom From (defaults to SMTP_FROM).
    - `reply_to`     → Reply-To header.
    - `cc` / `bcc`   → additional recipients.
    - `attachments`  → list of URLs to attach.
    """

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "user@example.com",
                "subject": "Welcome!",
                "body": "Thanks for signing up.",
                "from_email": "noreply@shopx.com",
                "reply_to": "support@shopx.com",
                "cc": ["team@example.com"],
                "bcc": ["audit@example.com"],
                "attachments": ["https://cdn.x.com/welcome.pdf"],
            }
        }
    }

    user_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Recipient identifier in the Tenant's system.",
        examples=["user@example.com"],
    )

    # Content (required for email)
    subject: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Email subject line.",
        examples=["Welcome!"],
    )
    body: str = Field(
        ...,
        min_length=1,
        description="Email body (plain text).",
        examples=["Thanks for signing up."],
    )

    # Email-specific (optional)
    from_email: EmailStr | None = Field(
        default=None,
        description=(
            "Override the default From address. "
            "If unset, the server default (SMTP_FROM) is used."
        ),
        examples=["noreply@shopx.com"],
    )
    reply_to: EmailStr | None = Field(
        default=None,
        description="Reply-To address.",
        examples=["support@shopx.com"],
    )
    cc: list[EmailStr] | None = Field(
        default=None,
        max_length=100,
        description="Carbon-copy recipients.",
    )
    bcc: list[EmailStr] | None = Field(
        default=None,
        max_length=100,
        description="Blind carbon-copy recipients.",
    )
    attachments: list[str] | None = Field(
        default=None,
        max_length=10,
        description="URLs of files to attach (max 10).",
    )

    # Validators
    # Remove duplicates while preserving order.
    @field_validator("cc", "bcc", "attachments")
    @classmethod
    def _dedupe(cls, v: list | None) -> list | None:
        if v is None:
            return None
        # dict.fromkeys preserves order and removes duplicates
        return list(dict.fromkeys(v)) or None
