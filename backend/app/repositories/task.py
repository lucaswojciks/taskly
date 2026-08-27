"""Task data access."""

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.task import Task
from app.models.task_tag import TaskTag
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    model = Task

    async def list_by_project(
        self, project_id: uuid.UUID, *, limit: int, offset: int
    ) -> Sequence[Task]:
        stmt = (
            select(Task)
            .where(Task.project_id == project_id)
            .options(selectinload(Task.task_tags).selectinload(TaskTag.tag))
            .order_by(Task.created_at.desc(), Task.id.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_in_project(
        self, project_id: uuid.UUID, task_id: uuid.UUID, *, refresh: bool = False
    ) -> Task | None:
        stmt = (
            select(Task)
            .where(Task.id == task_id, Task.project_id == project_id)
            .options(selectinload(Task.task_tags).selectinload(TaskTag.tag))
        )
        if refresh:
            # Force already-loaded instances (and their tag collection) to
            # refresh, so callers see writes made earlier in this transaction.
            stmt = stmt.execution_options(populate_existing=True)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
