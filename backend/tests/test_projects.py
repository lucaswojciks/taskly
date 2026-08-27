"""Integration tests for Project endpoints.

Spec: ``docs/specs/projects-tasks-tags.md``. Written before the implementation
exists: the ``/projects`` routes are not registered yet, so every test fails
with 404 (route missing) or at a setup helper. That is a valid "red".
"""

import pytest
from httpx import AsyncClient

from tests.helpers import (
    Headers,
    NewUser,
    create_project,
    create_project_id,
    create_task_id,
)


async def test_create_project_valid_returns_201(client: AsyncClient, auth_headers: Headers) -> None:
    response = await client.post("/projects", json={"name": "Website"}, headers=auth_headers)

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Website"
    assert "id" in body
    assert "created_at" in body
    assert "updated_at" in body


@pytest.mark.parametrize("name", ["", "   ", "\t\n"])
async def test_create_project_blank_name_returns_422(
    client: AsyncClient, auth_headers: Headers, name: str
) -> None:
    response = await client.post("/projects", json={"name": name}, headers=auth_headers)

    assert response.status_code == 422


async def test_list_projects_is_isolated_per_user(client: AsyncClient, new_user: NewUser) -> None:
    alice = await new_user()
    bob = await new_user()

    await client.post("/projects", json={"name": "Alice project"}, headers=alice)
    await client.post("/projects", json={"name": "Bob project"}, headers=bob)

    alice_list = await client.get("/projects", headers=alice)
    assert alice_list.status_code == 200
    assert [p["name"] for p in alice_list.json()] == ["Alice project"]

    bob_list = await client.get("/projects", headers=bob)
    assert bob_list.status_code == 200
    assert [p["name"] for p in bob_list.json()] == ["Bob project"]


async def test_get_project_detail_own_and_foreign(client: AsyncClient, new_user: NewUser) -> None:
    alice = await new_user()
    bob = await new_user()
    project_id = await create_project_id(client, alice, name="Alice project")

    own = await client.get(f"/projects/{project_id}", headers=alice)
    assert own.status_code == 200
    assert own.json()["id"] == project_id

    foreign = await client.get(f"/projects/{project_id}", headers=bob)
    assert foreign.status_code == 404
    assert foreign.json()["error"]["code"] == "resource_not_found"


async def test_update_project_own_and_foreign(client: AsyncClient, new_user: NewUser) -> None:
    alice = await new_user()
    bob = await new_user()
    project_id = await create_project_id(client, alice)

    updated = await client.patch(f"/projects/{project_id}", json={"name": "Renamed"}, headers=alice)
    assert updated.status_code == 200
    assert updated.json()["name"] == "Renamed"

    foreign = await client.patch(f"/projects/{project_id}", json={"name": "Hijacked"}, headers=bob)
    assert foreign.status_code == 404


async def test_patch_project_empty_body_is_noop(client: AsyncClient, auth_headers: Headers) -> None:
    project_id = await create_project_id(client, auth_headers, name="Stable name")

    response = await client.patch(f"/projects/{project_id}", json={}, headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["name"] == "Stable name"


async def test_delete_project_own_and_foreign(client: AsyncClient, new_user: NewUser) -> None:
    alice = await new_user()
    bob = await new_user()
    project_id = await create_project_id(client, alice)

    foreign = await client.delete(f"/projects/{project_id}", headers=bob)
    assert foreign.status_code == 404

    deleted = await client.delete(f"/projects/{project_id}", headers=alice)
    assert deleted.status_code == 204

    gone = await client.get(f"/projects/{project_id}", headers=alice)
    assert gone.status_code == 404


async def test_delete_project_cascades_to_tasks(client: AsyncClient, auth_headers: Headers) -> None:
    project_id = await create_project_id(client, auth_headers)
    task_id = await create_task_id(client, auth_headers, project_id)

    deleted = await client.delete(f"/projects/{project_id}", headers=auth_headers)
    assert deleted.status_code == 204

    # the task disappeared together with its project
    task = await client.get(f"/projects/{project_id}/tasks/{task_id}", headers=auth_headers)
    assert task.status_code == 404


async def test_list_projects_pagination(client: AsyncClient, auth_headers: Headers) -> None:
    for index in range(3):
        await client.post("/projects", json={"name": f"P{index}"}, headers=auth_headers)

    first_page = await client.get("/projects?limit=2&offset=0", headers=auth_headers)
    assert first_page.status_code == 200
    assert len(first_page.json()) == 2

    second_page = await client.get("/projects?limit=2&offset=2", headers=auth_headers)
    assert second_page.status_code == 200
    assert len(second_page.json()) == 1


@pytest.mark.parametrize("query", ["limit=0", "limit=201", "offset=-1"])
async def test_list_projects_pagination_out_of_range_returns_422(
    client: AsyncClient, auth_headers: Headers, query: str
) -> None:
    response = await client.get(f"/projects?{query}", headers=auth_headers)

    assert response.status_code == 422


async def test_duplicate_project_name_is_allowed(
    client: AsyncClient, auth_headers: Headers
) -> None:
    first = await create_project(client, auth_headers, name="Personal")
    second = await create_project(client, auth_headers, name="Personal")

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] != second.json()["id"]
