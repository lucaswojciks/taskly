"""Task routes, nested under a project. HTTP layer only."""

import uuid

from fastapi import APIRouter, status

from app.core.dependencies import DbSession, OwnedProject, PaginationParams
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.services.task_service import TaskService

router = APIRouter(prefix="/projects/{project_id}/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskRead])
async def list_tasks(
    project: OwnedProject, session: DbSession, page: PaginationParams
) -> list[TaskRead]:
    tasks = await TaskService(session).list_for_project(
        project, limit=page.limit, offset=page.offset
    )
    return [TaskRead.model_validate(task) for task in tasks]


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(payload: TaskCreate, project: OwnedProject, session: DbSession) -> TaskRead:
    task = await TaskService(session).create(project, payload)
    return TaskRead.model_validate(task)


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(task_id: uuid.UUID, project: OwnedProject, session: DbSession) -> TaskRead:
    task = await TaskService(session).get(project, task_id)
    return TaskRead.model_validate(task)


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: uuid.UUID, payload: TaskUpdate, project: OwnedProject, session: DbSession
) -> TaskRead:
    task = await TaskService(session).update(project, task_id, payload)
    return TaskRead.model_validate(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: uuid.UUID, project: OwnedProject, session: DbSession) -> None:
    await TaskService(session).delete(project, task_id)
