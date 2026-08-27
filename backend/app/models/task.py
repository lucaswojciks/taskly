"""Task model and its status enum."""

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.attachment import Attachment
    from app.models.project import Project
    from app.models.tag import Tag
    from app.models.task_tag import TaskTag


class TaskStatus(enum.StrEnum):
    not_started = "not_started"
    in_progress = "in_progress"
    done = "done"
    cancelled = "cancelled"


class Task(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "tasks"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    short_description: Mapped[str] = mapped_column(String, nullable=False)
    full_description: Mapped[str] = mapped_column(Text, nullable=False)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status"),
        default=TaskStatus.not_started,
        server_default=TaskStatus.not_started.value,
        nullable=False,
    )

    project: Mapped["Project"] = relationship(back_populates="tasks")

    attachments: Mapped[list["Attachment"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    task_tags: Mapped[list["TaskTag"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def tags(self) -> list["Tag"]:
        """Tags linked to this task.

        Read-only view over ``task_tags``; both ``task_tags`` and their ``tag``
        must be eagerly loaded by the caller (the task repository does this).
        """
        return [task_tag.tag for task_tag in self.task_tags]
