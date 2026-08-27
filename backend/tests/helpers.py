"""Shared helpers for the integration test suite.

The ``*_id`` helpers assert the setup call succeeded and return the new
resource's id, so a missing route shows up as a legible
"setup: POST ... expected 201, got 404" failure rather than a ``KeyError``.
"""

from collections.abc import Awaitable, Callable
from typing import Any

from httpx import AsyncClient, Response

Headers = dict[str, str]
NewUser = Callable[..., Awaitable[Headers]]

MINIMAL_TASK: dict[str, Any] = {
    "title": "A task",
    "short_description": "Short summary",
}


async def create_project(
    client: AsyncClient, headers: Headers, *, name: str = "My Project"
) -> Response:
    return await client.post("/projects", json={"name": name}, headers=headers)


async def create_project_id(
    client: AsyncClient, headers: Headers, *, name: str = "My Project"
) -> str:
    response = await create_project(client, headers, name=name)
    assert response.status_code == 201, (
        f"setup: POST /projects expected 201, got {response.status_code}: {response.text}"
    )
    project_id = response.json()["id"]
    assert isinstance(project_id, str)
    return project_id


async def create_tag(
    client: AsyncClient, headers: Headers, project_id: str, *, name: str = "urgent"
) -> Response:
    return await client.post(f"/projects/{project_id}/tags", json={"name": name}, headers=headers)


async def create_tag_id(
    client: AsyncClient, headers: Headers, project_id: str, *, name: str = "urgent"
) -> str:
    response = await create_tag(client, headers, project_id, name=name)
    assert response.status_code == 201, (
        f"setup: create tag expected 201, got {response.status_code}: {response.text}"
    )
    tag_id = response.json()["id"]
    assert isinstance(tag_id, str)
    return tag_id


async def create_task(
    client: AsyncClient, headers: Headers, project_id: str, **overrides: Any
) -> Response:
    payload = {**MINIMAL_TASK, **overrides}
    return await client.post(f"/projects/{project_id}/tasks", json=payload, headers=headers)


async def create_task_id(
    client: AsyncClient, headers: Headers, project_id: str, **overrides: Any
) -> str:
    response = await create_task(client, headers, project_id, **overrides)
    assert response.status_code == 201, (
        f"setup: create task expected 201, got {response.status_code}: {response.text}"
    )
    task_id = response.json()["id"]
    assert isinstance(task_id, str)
    return task_id
