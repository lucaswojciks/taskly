"""Project data access."""

import uuid
from collections.abc import Sequence

from sqlalchemy import select

from app.models.project import Project
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    model = Project

    async def list_by_owner(
        self, owner_id: uuid.UUID, *, limit: int, offset: int
    ) -> Sequence[Project]:
        stmt = (
            select(Project)
            .where(Project.owner_id == owner_id)
            .order_by(Project.created_at.desc(), Project.id.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_owned(self, project_id: uuid.UUID, owner_id: uuid.UUID) -> Project | None:
        stmt = select(Project).where(Project.id == project_id, Project.owner_id == owner_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
