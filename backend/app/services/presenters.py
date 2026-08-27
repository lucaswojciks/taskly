"""Build read schemas from ORM models, including storage-dependent fields.

Kept out of the schema modules so that ``AttachmentRead`` / ``TaskRead`` stay
free of any storage-client dependency or validation context.
"""

from app.core.storage import ObjectStorage
from app.models.attachment import Attachment
from app.models.task import Task
from app.schemas.attachment import AttachmentRead
from app.schemas.tag import TagRead
from app.schemas.task import TaskRead


def attachment_to_read(attachment: Attachment, storage: ObjectStorage) -> AttachmentRead:
    return AttachmentRead(
        id=attachment.id,
        file_name=attachment.file_name,
        content_type=attachment.content_type,
        uploaded_at=attachment.uploaded_at,
        url=storage.presigned_get_url(attachment.file_url),
    )


def task_to_read(task: Task, storage: ObjectStorage) -> TaskRead:
    return TaskRead(
        id=task.id,
        project_id=task.project_id,
        title=task.title,
        short_description=task.short_description,
        full_description=task.full_description,
        deadline=task.deadline,
        status=task.status,
        tags=[TagRead.model_validate(tag) for tag in task.tags],
        attachments=[attachment_to_read(item, storage) for item in task.attachments],
        created_at=task.created_at,
        updated_at=task.updated_at,
    )
