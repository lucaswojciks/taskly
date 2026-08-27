"""Tag business rules."""

from collections.abc import Sequence

from app.models.project import Project
from app.models.tag import Tag
from app.repositories.tag import TagRepository
from app.schemas.tag import TagCreate
from app.services.base import BaseService


class TagService(BaseService):
    @property
    def _tags(self) -> TagRepository:
        return TagRepository(self.session)

    async def create(self, project: Project, data: TagCreate) -> Tag:
        return await self._tags.create(name=data.name, project_id=project.id)

    async def list_for_project(self, project: Project, *, limit: int, offset: int) -> Sequence[Tag]:
        return await self._tags.list_by_project(project.id, limit=limit, offset=offset)
