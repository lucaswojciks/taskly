"""TaskTag data access."""

from app.models.task_tag import TaskTag
from app.repositories.base import BaseRepository


class TaskTagRepository(BaseRepository[TaskTag]):
    model = TaskTag
