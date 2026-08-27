"""Project business rules."""

import uuid
from collections.abc import Sequence

from sqlalchemy import delete

from app.models.project import Project
from app.repositories.project import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.base import BaseService


class ProjectService(BaseService):
    @property
    def _projects(self) -> ProjectRepository:
        return ProjectRepository(self.session)

    async def create(self, owner_id: uuid.UUID, data: ProjectCreate) -> Project:
        return await self._projects.create(name=data.name, owner_id=owner_id)

    async def list_for_owner(
        self, owner_id: uuid.UUID, *, limit: int, offset: int
    ) -> Sequence[Project]:
        return await self._projects.list_by_owner(owner_id, limit=limit, offset=offset)

    async def update(self, project: Project, data: ProjectUpdate) -> Project:
        applied = False
        for field in data.model_fields_set:
            value = getattr(data, field)
            if value is None:
                continue
            setattr(project, field, value)
            applied = True

        if applied:
            await self.session.flush()
            await self.session.refresh(project)
        return project

    async def delete(self, project: Project) -> None:
        # A single DELETE; Postgres cascades to tasks, tags and, from those, to
        # task_tags and attachments (spec §4.3).
        await self.session.execute(delete(Project).where(Project.id == project.id))
        await self.session.flush()
