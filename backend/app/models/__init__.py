"""SQLAlchemy models package.

Every model module is imported here so that ``Base.metadata`` is fully populated
for Alembic autogenerate and for the test-suite table creation.
"""

from app.models.attachment import Attachment
from app.models.base import TimestampMixin, UUIDMixin
from app.models.project import Project
from app.models.tag import Tag
from app.models.task import Task, TaskStatus
from app.models.task_tag import TaskTag
from app.models.user import User

__all__ = [
    "Attachment",
    "Project",
    "Tag",
    "Task",
    "TaskStatus",
    "TaskTag",
    "TimestampMixin",
    "UUIDMixin",
    "User",
]
