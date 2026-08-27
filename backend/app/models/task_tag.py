"""TaskTag association model (Task <-> Tag, many-to-many)."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.tag import Tag
    from app.models.task import Task


class TaskTag(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "task_tags"
    __table_args__ = (UniqueConstraint("task_id", "tag_id", name="uq_task_tags_task_id_tag_id"),)

    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    task: Mapped["Task"] = relationship(back_populates="task_tags")
    tag: Mapped["Tag"] = relationship(back_populates="task_tags")
