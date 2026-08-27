"""Pydantic schemas for Attachments (see docs/specs/attachments.md).

``AttachmentRead`` is built explicitly by the service (with a fresh presigned
URL), not via ``model_validate`` — there is no storage-aware validation context.
"""

import datetime as dt
import uuid

from pydantic import BaseModel


class AttachmentRead(BaseModel):
    id: uuid.UUID
    file_name: str
    content_type: str
    uploaded_at: dt.datetime
    url: str
