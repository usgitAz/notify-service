from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class UUIDMIXIN:
    """UUID primery key with server default."""

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid(),
    )


class CreatedAtMixin:
    """created_at with timezone-aware."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class UpdatedAtMixin:
    """updated_at: last updated at orm level only."""

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class TimeStampMixin(CreatedAtMixin, UpdatedAtMixin):
    """Mix created_at and updated_at."""


class SoftDeleteMixin:
    """Soft delete with is_active and deactivated_at."""

    is_actve: Mapped[bool] = mapped_column(
        default=True, server_default="true", nullable=False, index=True
    )
    deactivated_at: Mapped[bool] = mapped_column(
        DateTime(timezone=True), nullable=False, default=None
    )
