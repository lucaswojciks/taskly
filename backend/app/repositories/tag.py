"""Tag data access."""

import uuid
from collections.abc import Sequence

from sqlalchemy import select

from app.models.tag import Tag
from app.repositories.base import BaseRepository


class TagRepository(BaseRepository[Tag]):
    model = Tag

    async def list_by_project(
        self, project_id: uuid.UUID, *, limit: int, offset: int
    ) -> Sequence[Tag]:
        stmt = (
            select(Tag)
            .where(Tag.project_id == project_id)
            .order_by(Tag.created_at.desc(), Tag.id.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_ids_in_project(
        self, project_id: uuid.UUID, tag_ids: Sequence[uuid.UUID]
    ) -> set[uuid.UUID]:
        """Return the subset of ``tag_ids`` that exist in the given project."""
        if not tag_ids:
            return set()
        stmt = select(Tag.id).where(Tag.project_id == project_id, Tag.id.in_(tag_ids))
        result = await self.session.execute(stmt)
        return set(result.scalars().all())
