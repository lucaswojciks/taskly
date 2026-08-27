"""Task routes, nested under a project. HTTP layer only."""

import uuid

from fastapi import APIRouter, status

from app.core.dependencies import DbSession, OwnedProject, PaginationParams
from app.core.storage import StorageDep
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.services.task_service import TaskService

router = APIRouter(prefix="/projects/{project_id}/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskRead])
async def list_tasks(
    project: OwnedProject, session: DbSession, storage: StorageDep, page: PaginationParams
) -> list[TaskRead]:
    return await TaskService(session, storage).list_for_project(
        project, limit=page.limit, offset=page.offset
    )


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate, project: OwnedProject, session: DbSession, storage: StorageDep
) -> TaskRead:
    return await TaskService(session, storage).create(project, payload)


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(
    task_id: uuid.UUID, project: OwnedProject, session: DbSession, storage: StorageDep
) -> TaskRead:
    return await TaskService(session, storage).get_detail(project, task_id)


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: uuid.UUID,
    payload: TaskUpdate,
    project: OwnedProject,
    session: DbSession,
    storage: StorageDep,
) -> TaskRead:
    return await TaskService(session, storage).update(project, task_id, payload)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: uuid.UUID, project: OwnedProject, session: DbSession, storage: StorageDep
) -> None:
    await TaskService(session, storage).delete(project, task_id)
