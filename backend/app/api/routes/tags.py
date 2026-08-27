"""Tag routes, nested under a project. HTTP layer only."""

from fastapi import APIRouter, status

from app.core.dependencies import DbSession, OwnedProject, PaginationParams
from app.schemas.tag import TagCreate, TagRead
from app.services.tag_service import TagService

router = APIRouter(prefix="/projects/{project_id}/tags", tags=["tags"])


@router.get("", response_model=list[TagRead])
async def list_tags(
    project: OwnedProject, session: DbSession, page: PaginationParams
) -> list[TagRead]:
    tags = await TagService(session).list_for_project(project, limit=page.limit, offset=page.offset)
    return [TagRead.model_validate(tag) for tag in tags]


@router.post("", response_model=TagRead, status_code=status.HTTP_201_CREATED)
async def create_tag(payload: TagCreate, project: OwnedProject, session: DbSession) -> TagRead:
    tag = await TagService(session).create(project, payload)
    return TagRead.model_validate(tag)
