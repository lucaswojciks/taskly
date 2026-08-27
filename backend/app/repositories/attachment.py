"""Attachment data access."""

import uuid

from sqlalchemy import select

from app.models.attachment import Attachment
from app.repositories.base import BaseRepository


class AttachmentRepository(BaseRepository[Attachment]):
    model = Attachment

    async def get_in_task(self, task_id: uuid.UUID, attachment_id: uuid.UUID) -> Attachment | None:
        stmt = select(Attachment).where(
            Attachment.id == attachment_id, Attachment.task_id == task_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
