"""Pydantic schemas for Tasks (see docs/specs/projects-tasks-tags.md)."""

import datetime as dt
import uuid

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from app.models.task import TaskStatus
from app.schemas.common import TrimmedStr
from app.schemas.tag import TagRead


class TaskCreate(BaseModel):
    """Body of ``POST /projects/{id}/tasks``."""

    title: TrimmedStr = Field(min_length=1, max_length=200)
    short_description: TrimmedStr = Field(min_length=1, max_length=500)
    full_description: str = Field(default="", max_length=20000)
    deadline: AwareDatetime | None = None
    status: TaskStatus = TaskStatus.not_started
    tag_ids: list[uuid.UUID] = Field(default_factory=list)


class TaskUpdate(BaseModel):
    """Body of ``PATCH /projects/{id}/tasks/{task_id}``.

    Every field is optional; only the fields present in the request are applied.
    ``deadline: null`` clears the deadline; ``tag_ids`` replaces the whole set.
    """

    title: TrimmedStr | None = Field(default=None, min_length=1, max_length=200)
    short_description: TrimmedStr | None = Field(default=None, min_length=1, max_length=500)
    full_description: str | None = Field(default=None, max_length=20000)
    deadline: AwareDatetime | None = None
    status: TaskStatus | None = None
    tag_ids: list[uuid.UUID] | None = None


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    short_description: str
    full_description: str
    deadline: dt.datetime | None
    status: TaskStatus
    tags: list[TagRead]
    created_at: dt.datetime
    updated_at: dt.datetime
