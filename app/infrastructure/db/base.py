"""
SQLAlchemy base classes and common mixins.

Provides:
- Base declarative class with consistent naming convention
- UUID primary key mixin
- Timestamp mixins (created_at / updated_at)
- Soft-delete mixin
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Consistent constraint naming for Alembic and PostgreSQL
NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class UUIDMixin:
    """
    UUID primary key mixin.

    Uses PostgreSQL gen_random_uuid() as server default.
    """

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid(),
    )


class CreatedAtMixin:
    """Adds a timezone-aware created_at column."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class UpdatedAtMixin:
    """
    Adds a timezone-aware updated_at column.

    Note: onupdate only triggers on ORM-level changes.
    """

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class TimestampMixin(CreatedAtMixin, UpdatedAtMixin):
    """Combines created_at and updated_at."""


class SoftDeleteMixin:
    """
    Soft-delete support.

    Records are never hard-deleted. Instead:
    - is_active is set to False
    - deactivated_at is filled with the deactivation timestamp

    Note: no single-column index on is_active (low cardinality).
    Add composite indexes per-table when needed.
    """

    is_active: Mapped[bool] = mapped_column(
        default=True,
        server_default="true",
        nullable=False,
    )
    deactivated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
