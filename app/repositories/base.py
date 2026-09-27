"""
Generic base repository.

Provides the most common DB operations for any SQLAlchemy model.
Subclasses set `model` to the concrete SQLAlchemy class.

Design:
- Stateless: `session` is passed to each method, not stored on self.
- No commits: transaction lifecycle is owned by the service layer.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.base import Base


class BaseRepository[ModelT: Base]:
    """Base class for all repositories."""

    model: type[ModelT]

    async def get(
        self,
        session: AsyncSession,
        obj_id: UUID,
    ) -> ModelT | None:
        """Fetch by primary key."""
        return await session.get(self.model, obj_id)

    async def add(
        self,
        session: AsyncSession,
        obj: ModelT,
    ) -> ModelT:
        """
        Add `obj` to the session and flush (no commit).

        Flush sends the INSERT and populates server-side defaults
        (id, created_at, updated_at). Commit is the caller's job.
        """
        session.add(obj)
        await session.flush()
        await session.refresh(obj)
        return obj

    async def delete(
        self,
        session: AsyncSession,
        obj: ModelT,
    ) -> None:
        """Mark `obj` for deletion (no commit)."""
        await session.delete(obj)
