"""Project routes. HTTP layer only — parse, call the service, return."""

from fastapi import APIRouter, status

from app.core.dependencies import CurrentUser, DbSession, OwnedProject, PaginationParams
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectRead])
async def list_projects(
    current_user: CurrentUser, session: DbSession, page: PaginationParams
) -> list[ProjectRead]:
    projects = await ProjectService(session).list_for_owner(
        current_user.id, limit=page.limit, offset=page.offset
    )
    return [ProjectRead.model_validate(project) for project in projects]


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate, current_user: CurrentUser, session: DbSession
) -> ProjectRead:
    project = await ProjectService(session).create(current_user.id, payload)
    return ProjectRead.model_validate(project)


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(project: OwnedProject) -> ProjectRead:
    return ProjectRead.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    project: OwnedProject, payload: ProjectUpdate, session: DbSession
) -> ProjectRead:
    updated = await ProjectService(session).update(project, payload)
    return ProjectRead.model_validate(updated)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project: OwnedProject, session: DbSession) -> None:
    await ProjectService(session).delete(project)
