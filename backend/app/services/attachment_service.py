"""Attachment business rules: upload and removal.

Order on upload: validate, then store the object, then create the row
(spec §4.4). Order on removal: delete the row, then best-effort delete the
object — an R2 failure never fails the request (spec §4.5).
"""

import logging
import uuid
from datetime import UTC, datetime

from fastapi import UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.files import SNIFF_BYTES, detect_content_type, extension_for, sanitize_filename
from app.core.storage import ObjectStorage
from app.exceptions.domain import (
    FileTooLargeError,
    ResourceNotFoundError,
    StorageError,
    UnsupportedFileTypeError,
)
from app.models.attachment import Attachment
from app.models.project import Project
from app.repositories.attachment import AttachmentRepository
from app.repositories.task import TaskRepository
from app.schemas.attachment import AttachmentRead
from app.services.base import BaseService
from app.services.presenters import attachment_to_read

logger = logging.getLogger(__name__)

_READ_CHUNK = 64 * 1024


class AttachmentService(BaseService):
    def __init__(self, session: AsyncSession, storage: ObjectStorage) -> None:
        super().__init__(session)
        self._storage = storage

    @property
    def _tasks(self) -> TaskRepository:
        return TaskRepository(self.session)

    @property
    def _attachments(self) -> AttachmentRepository:
        return AttachmentRepository(self.session)

    async def add(self, project: Project, task_id: uuid.UUID, upload: UploadFile) -> AttachmentRead:
        task = await self._tasks.get_in_project(project.id, task_id)
        if task is None:
            raise ResourceNotFoundError("Task not found.")

        data = await self._read_within_limit(upload)
        content_type = detect_content_type(data[:SNIFF_BYTES])
        if content_type is None:
            raise UnsupportedFileTypeError

        attachment_id = uuid.uuid4()
        key = f"attachments/{task_id}/{attachment_id}.{extension_for(content_type)}"

        try:
            await self._storage.put_object(key, data, content_type)
        except Exception as exc:
            raise StorageError from exc

        attachment = Attachment(
            id=attachment_id,
            file_url=key,
            file_name=sanitize_filename(upload.filename, content_type=content_type),
            content_type=content_type,
            uploaded_at=datetime.now(UTC),
        )
        task.attachments.append(attachment)
        try:
            await self.session.flush()
        except IntegrityError as exc:
            await self._best_effort_delete(key)
            raise ResourceNotFoundError("Task not found.") from exc

        return attachment_to_read(attachment, self._storage)

    async def remove(self, project: Project, task_id: uuid.UUID, attachment_id: uuid.UUID) -> None:
        task = await self._tasks.get_in_project(project.id, task_id)
        if task is None:
            raise ResourceNotFoundError("Task not found.")

        attachment = await self._attachments.get_in_task(task_id, attachment_id)
        if attachment is None:
            raise ResourceNotFoundError("Attachment not found.")

        key = attachment.file_url
        # Remove via the loaded collection so delete-orphan fires and the
        # in-session task.attachments stays consistent for later reads.
        task.attachments.remove(attachment)
        await self.session.flush()
        await self._best_effort_delete(key)

    async def _read_within_limit(self, upload: UploadFile) -> bytes:
        max_bytes = settings.attachment_max_bytes
        if upload.size is not None and upload.size > max_bytes:
            raise FileTooLargeError(f"The file exceeds the {max_bytes} byte limit.")

        chunks: list[bytes] = []
        total = 0
        while chunk := await upload.read(_READ_CHUNK):
            total += len(chunk)
            if total > max_bytes:
                raise FileTooLargeError(f"The file exceeds the {max_bytes} byte limit.")
            chunks.append(chunk)
        return b"".join(chunks)

    async def _best_effort_delete(self, key: str) -> None:
        try:
            await self._storage.delete_object(key)
        except Exception:
            logger.warning("failed to delete object %s from storage", key, exc_info=True)
