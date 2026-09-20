"""
User model.

Represents an end-user belonging to a Tenant.
external_id is the identifier used by the Tenant's own system.

Records are never hard-deleted; only soft-deleted via is_active.
"""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.infrastructure.db.models.device import Device
    from app.infrastructure.db.models.notification import Notification
    from app.infrastructure.db.models.tenant import Tenant


class User(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    """End-user that can receive notifications."""

    __tablename__ = "users"

    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Identifier in the Tenant's own system
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)

    email: Mapped[str | None] = mapped_column(String(320), nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="users")

    devices: Mapped[list["Device"]] = relationship(
        back_populates="user",
        lazy="selectin",
    )
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="user",
        lazy="selectin",
    )

    __table_args__ = (
        Index(
            "uq_users_tenant_external_active",
            "tenant_id",
            "external_id",
            unique=True,
            postgresql_where=text("is_active = true"),
        ),
        Index("ix_users_tenant_active", "tenant_id", "is_active"),
    )

    def __repr__(self) -> str:
        return (
            f"<User id={self.id} external_id={self.external_id} "
            f"active={self.is_active}>"
        )
