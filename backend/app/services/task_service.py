"""Task business rules.

Tag-id validation is atomic: if any id is unknown or belongs to another
project, the whole create/update is rejected with ``InvalidTagIdsError`` and
nothing is persisted (spec §4.2).
"""

import uuid
from collections.abc import Sequence

from sqlalchemy import delete

from app.exceptions.domain import InvalidTagIdsError, ResourceNotFoundError
from app.models.project import Project
from app.models.task import Task
from app.repositories.tag import TagRepository
from app.repositories.task import TaskRepository
from app.repositories.task_tag import TaskTagRepository
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.base import BaseService

# PATCH fields where an explicit ``null`` is meaningful (clears the value)
# rather than "leave unchanged".
_NULLABLE_UPDATE_FIELDS = {"deadline"}


def _deduplicate(tag_ids: Sequence[uuid.UUID]) -> list[uuid.UUID]:
    return list(dict.fromkeys(tag_ids))


class TaskService(BaseService):
    @property
    def _tasks(self) -> TaskRepository:
        return TaskRepository(self.session)

    @property
    def _tags(self) -> TagRepository:
        return TagRepository(self.session)

    @property
    def _task_tags(self) -> TaskTagRepository:
        return TaskTagRepository(self.session)

    async def create(self, project: Project, data: TaskCreate) -> Task:
        tag_ids = _deduplicate(data.tag_ids)
        await self._require_tags_in_project(project.id, tag_ids)

        task = Task(
            project_id=project.id,
            title=data.title,
            short_description=data.short_description,
            full_description=data.full_description,
            deadline=data.deadline,
            status=data.status,
        )
        self.session.add(task)
        await self.session.flush()
        await self._task_tags.replace_task_tags(task.id, tag_ids)
        return await self._reload(project.id, task.id)

    async def list_for_project(
        self, project: Project, *, limit: int, offset: int
    ) -> Sequence[Task]:
        return await self._tasks.list_by_project(project.id, limit=limit, offset=offset)

    async def get(self, project: Project, task_id: uuid.UUID) -> Task:
        task = await self._tasks.get_in_project(project.id, task_id)
        if task is None:
            raise ResourceNotFoundError("Task not found.")
        return task

    async def update(self, project: Project, task_id: uuid.UUID, data: TaskUpdate) -> Task:
        task = await self.get(project, task_id)

        replace_tags = "tag_ids" in data.model_fields_set
        new_tag_ids: list[uuid.UUID] = []
        if replace_tags:
            new_tag_ids = _deduplicate(data.tag_ids or [])
            await self._require_tags_in_project(project.id, new_tag_ids)

        for field in data.model_fields_set:
            if field == "tag_ids":
                continue
            value = getattr(data, field)
            if value is None and field not in _NULLABLE_UPDATE_FIELDS:
                continue
            setattr(task, field, value)

        if replace_tags:
            await self._task_tags.replace_task_tags(task_id, new_tag_ids)

        await self.session.flush()
        return await self._reload(project.id, task_id)

    async def delete(self, project: Project, task_id: uuid.UUID) -> None:
        task = await self.get(project, task_id)
        # Postgres cascades to task_tags and attachments; the tags survive.
        await self.session.execute(delete(Task).where(Task.id == task.id))
        await self.session.flush()

    async def _reload(self, project_id: uuid.UUID, task_id: uuid.UUID) -> Task:
        task = await self._tasks.get_in_project(project_id, task_id, refresh=True)
        if task is None:  # pragma: no cover - the row was just written
            raise ResourceNotFoundError("Task not found.")
        return task

    async def _require_tags_in_project(
        self, project_id: uuid.UUID, tag_ids: Sequence[uuid.UUID]
    ) -> None:
        if not tag_ids:
            return
        found = await self._tags.get_ids_in_project(project_id, tag_ids)
        if found != set(tag_ids):
            raise InvalidTagIdsError
