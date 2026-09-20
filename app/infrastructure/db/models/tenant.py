"""
Tenant model.

A Tenant represents a customer of the Notification Service
(the entity that owns an API key and can send notifications).

Records are never hard-deleted; only soft-deleted via is_active.
"""

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.infrastructure.db.models.notification import Notification
    from app.infrastructure.db.models.user import User


class Tenant(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Customer of the notification service (API key owner)."""

    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    api_key_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    # Relationships
    users: Mapped[list["User"]] = relationship(
        back_populates="tenant",
        lazy="selectin",
    )
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="tenant",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Tenant id={self.id} name={self.name} active={self.is_active}>"
