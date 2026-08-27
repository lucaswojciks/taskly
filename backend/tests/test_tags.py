"""Integration tests for Tag endpoints.

Spec: ``docs/specs/projects-tasks-tags.md``. Written before the implementation
exists: the ``/projects/{id}/tags`` routes are not registered yet.
"""

from httpx import AsyncClient

from tests.helpers import Headers, NewUser, create_project_id, create_tag_id


async def test_create_tag_valid_returns_201(client: AsyncClient, auth_headers: Headers) -> None:
    project_id = await create_project_id(client, auth_headers)

    response = await client.post(
        f"/projects/{project_id}/tags", json={"name": "urgent"}, headers=auth_headers
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "urgent"
    assert body["project_id"] == project_id
    assert "id" in body


async def test_create_tag_in_foreign_project_returns_404(
    client: AsyncClient, new_user: NewUser
) -> None:
    alice = await new_user()
    bob = await new_user()
    project_id = await create_project_id(client, alice)

    response = await client.post(
        f"/projects/{project_id}/tags", json={"name": "sneaky"}, headers=bob
    )

    assert response.status_code == 404


async def test_list_tags_of_project(client: AsyncClient, auth_headers: Headers) -> None:
    project_id = await create_project_id(client, auth_headers)
    await create_tag_id(client, auth_headers, project_id, name="a")
    await create_tag_id(client, auth_headers, project_id, name="b")

    response = await client.get(f"/projects/{project_id}/tags", headers=auth_headers)

    assert response.status_code == 200
    assert {tag["name"] for tag in response.json()} == {"a", "b"}


async def test_duplicate_tag_name_in_same_project_is_allowed(
    client: AsyncClient, auth_headers: Headers
) -> None:
    project_id = await create_project_id(client, auth_headers)

    first = await client.post(
        f"/projects/{project_id}/tags", json={"name": "dup"}, headers=auth_headers
    )
    second = await client.post(
        f"/projects/{project_id}/tags", json={"name": "dup"}, headers=auth_headers
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] != second.json()["id"]
