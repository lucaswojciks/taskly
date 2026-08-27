"""Attachment routes, nested under a task. HTTP layer only."""

import uuid
from typing import Annotated

from fastapi import APIRouter, File, UploadFile, status

from app.core.dependencies import DbSession, OwnedProject
from app.core.storage import StorageDep
from app.schemas.attachment import AttachmentRead
from app.services.attachment_service import AttachmentService

router = APIRouter(
    prefix="/projects/{project_id}/tasks/{task_id}/attachments", tags=["attachments"]
)


@router.post("", response_model=AttachmentRead, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    task_id: uuid.UUID,
    project: OwnedProject,
    session: DbSession,
    storage: StorageDep,
    file: Annotated[UploadFile, File()],
) -> AttachmentRead:
    return await AttachmentService(session, storage).add(project, task_id, file)


@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
    task_id: uuid.UUID,
    attachment_id: uuid.UUID,
    project: OwnedProject,
    session: DbSession,
    storage: StorageDep,
) -> None:
    await AttachmentService(session, storage).remove(project, task_id, attachment_id)
