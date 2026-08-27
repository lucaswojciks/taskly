"""Pydantic schemas for Tags (see docs/specs/projects-tasks-tags.md)."""

import datetime as dt
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import TrimmedStr


class TagCreate(BaseModel):
    """Body of ``POST /projects/{id}/tags``."""

    name: TrimmedStr = Field(min_length=1, max_length=50)


class TagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    created_at: dt.datetime
    updated_at: dt.datetime
