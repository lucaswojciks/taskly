"""TaskTag data access."""

import uuid
from collections.abc import Sequence

from sqlalchemy import delete

from app.models.task_tag import TaskTag
from app.repositories.base import BaseRepository


class TaskTagRepository(BaseRepository[TaskTag]):
    model = TaskTag

    async def replace_task_tags(self, task_id: uuid.UUID, tag_ids: Sequence[uuid.UUID]) -> None:
        """Make the task's tag associations exactly ``tag_ids``.

        Callers are responsible for deduplicating and validating ``tag_ids``.
        """
        await self.session.execute(delete(TaskTag).where(TaskTag.task_id == task_id))
        self.session.add_all(TaskTag(task_id=task_id, tag_id=tag_id) for tag_id in tag_ids)
        await self.session.flush()
