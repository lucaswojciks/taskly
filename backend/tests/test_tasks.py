"""Integration tests for Task endpoints.

Spec: ``docs/specs/projects-tasks-tags.md``. Written before the implementation
exists: the ``/projects/{id}/tasks`` routes are not registered yet.
"""

import uuid

import pytest
from httpx import AsyncClient

from tests.helpers import (
    Headers,
    NewUser,
    create_project_id,
    create_tag_id,
    create_task,
    create_task_id,
)

PAST_DEADLINE = "2020-01-01T00:00:00Z"
FUTURE_DEADLINE = "2030-09-01T18:00:00Z"


async def test_create_task_minimal_uses_defaults(
    client: AsyncClient, auth_headers: Headers
) -> None:
    project_id = await create_project_id(client, auth_headers)

    response = await client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "Do the thing", "short_description": "a summary"},
        headers=auth_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Do the thing"
    assert body["full_description"] == ""
    assert body["status"] == "not_started"
    assert body["deadline"] is None
    assert body["tags"] == []
    assert body["project_id"] == project_id


@pytest.mark.parametrize(
    "payload",
    [
        {"short_description": "no title"},
        {"title": "no short description"},
        {"title": "", "short_description": "blank title"},
        {"title": "   ", "short_description": "whitespace title"},
        {"title": "ok", "short_description": ""},
    ],
)
async def test_create_task_missing_or_blank_required_fields_returns_422(
    client: AsyncClient, auth_headers: Headers, payload: dict[str, str]
) -> None:
    project_id = await create_project_id(client, auth_headers)

    response = await client.post(
        f"/projects/{project_id}/tasks", json=payload, headers=auth_headers
    )

    assert response.status_code == 422


async def test_create_task_in_foreign_project_returns_404(
    client: AsyncClient, new_user: NewUser
) -> None:
    alice = await new_user()
    bob = await new_user()
    project_id = await create_project_id(client, alice)

    response = await client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "x", "short_description": "y"},
        headers=bob,
    )

    assert response.status_code == 404


async def test_create_task_with_valid_tag_ids(client: AsyncClient, auth_headers: Headers) -> None:
    project_id = await create_project_id(client, auth_headers)
    tag_a = await create_tag_id(client, auth_headers, project_id, name="urgent")
    tag_b = await create_tag_id(client, auth_headers, project_id, name="backend")

    response = await client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "x", "short_description": "y", "tag_ids": [tag_a, tag_b]},
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert {tag["id"] for tag in response.json()["tags"]} == {tag_a, tag_b}


async def test_create_task_with_unknown_tag_id_returns_422_and_persists_nothing(
    client: AsyncClient, auth_headers: Headers
) -> None:
    project_id = await create_project_id(client, auth_headers)
    unknown_tag = str(uuid.uuid4())

    response = await client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "x", "short_description": "y", "tag_ids": [unknown_tag]},
        headers=auth_headers,
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_tag_ids"

    listing = await client.get(f"/projects/{project_id}/tasks", headers=auth_headers)
    assert listing.status_code == 200
    assert listing.json() == []


async def test_create_task_with_tag_from_other_project_returns_422(
    client: AsyncClient, auth_headers: Headers
) -> None:
    project_a = await create_project_id(client, auth_headers, name="A")
    project_b = await create_project_id(client, auth_headers, name="B")
    foreign_tag = await create_tag_id(client, auth_headers, project_b, name="b-only")

    response = await client.post(
        f"/projects/{project_a}/tasks",
        json={"title": "x", "short_description": "y", "tag_ids": [foreign_tag]},
        headers=auth_headers,
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_tag_ids"


async def test_create_task_deduplicates_tag_ids(client: AsyncClient, auth_headers: Headers) -> None:
    project_id = await create_project_id(client, auth_headers)
    tag = await create_tag_id(client, auth_headers, project_id)

    response = await client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "x", "short_description": "y", "tag_ids": [tag, tag, tag]},
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert [t["id"] for t in response.json()["tags"]] == [tag]


async def test_list_tasks_of_project(client: AsyncClient, auth_headers: Headers) -> None:
    project_id = await create_project_id(client, auth_headers)
    await create_task_id(client, auth_headers, project_id)
    await create_task_id(client, auth_headers, project_id)

    response = await client.get(f"/projects/{project_id}/tasks", headers=auth_headers)

    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_task_detail_isolation(client: AsyncClient, new_user: NewUser) -> None:
    alice = await new_user()
    bob = await new_user()
    project_id = await create_project_id(client, alice)
    task_id = await create_task_id(client, alice, project_id)

    own = await client.get(f"/projects/{project_id}/tasks/{task_id}", headers=alice)
    assert own.status_code == 200
    assert own.json()["id"] == task_id

    foreign = await client.get(f"/projects/{project_id}/tasks/{task_id}", headers=bob)
    assert foreign.status_code == 404

    other_project = await create_project_id(client, alice, name="Other")
    wrong_project = await client.get(f"/projects/{other_project}/tasks/{task_id}", headers=alice)
    assert wrong_project.status_code == 404


async def test_update_task_status(client: AsyncClient, auth_headers: Headers) -> None:
    project_id = await create_project_id(client, auth_headers)
    task_id = await create_task_id(client, auth_headers, project_id)

    response = await client.patch(
        f"/projects/{project_id}/tasks/{task_id}",
        json={"status": "in_progress"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"


async def test_update_task_tag_ids_replaces_the_whole_set(
    client: AsyncClient, auth_headers: Headers
) -> None:
    project_id = await create_project_id(client, auth_headers)
    tag_a = await create_tag_id(client, auth_headers, project_id, name="a")
    tag_b = await create_tag_id(client, auth_headers, project_id, name="b")
    tag_c = await create_tag_id(client, auth_headers, project_id, name="c")
    task_id = await create_task_id(client, auth_headers, project_id, tag_ids=[tag_a, tag_b])

    response = await client.patch(
        f"/projects/{project_id}/tasks/{task_id}",
        json={"tag_ids": [tag_c]},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert [tag["id"] for tag in response.json()["tags"]] == [tag_c]


async def test_update_task_tag_ids_empty_removes_all_tags(
    client: AsyncClient, auth_headers: Headers
) -> None:
    project_id = await create_project_id(client, auth_headers)
    tag = await create_tag_id(client, auth_headers, project_id)
    task_id = await create_task_id(client, auth_headers, project_id, tag_ids=[tag])

    response = await client.patch(
        f"/projects/{project_id}/tasks/{task_id}",
        json={"tag_ids": []},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["tags"] == []


async def test_update_task_deadline_to_null_clears_it(
    client: AsyncClient, auth_headers: Headers
) -> None:
    project_id = await create_project_id(client, auth_headers)
    task_id = await create_task_id(client, auth_headers, project_id, deadline=FUTURE_DEADLINE)

    response = await client.patch(
        f"/projects/{project_id}/tasks/{task_id}",
        json={"deadline": None},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["deadline"] is None


async def test_create_task_with_past_deadline_is_accepted(
    client: AsyncClient, auth_headers: Headers
) -> None:
    project_id = await create_project_id(client, auth_headers)

    response = await create_task(client, auth_headers, project_id, deadline=PAST_DEADLINE)

    assert response.status_code == 201
    assert response.json()["deadline"] is not None


async def test_create_task_with_naive_deadline_returns_422(
    client: AsyncClient, auth_headers: Headers
) -> None:
    project_id = await create_project_id(client, auth_headers)

    response = await create_task(client, auth_headers, project_id, deadline="2026-09-01T18:00:00")

    assert response.status_code == 422


async def test_delete_task_removes_it_and_keeps_tags(
    client: AsyncClient, auth_headers: Headers
) -> None:
    project_id = await create_project_id(client, auth_headers)
    tag = await create_tag_id(client, auth_headers, project_id)
    task_id = await create_task_id(client, auth_headers, project_id, tag_ids=[tag])

    deleted = await client.delete(f"/projects/{project_id}/tasks/{task_id}", headers=auth_headers)
    assert deleted.status_code == 204

    gone = await client.get(f"/projects/{project_id}/tasks/{task_id}", headers=auth_headers)
    assert gone.status_code == 404

    # the tag itself is untouched by deleting a task that used it
    tags = await client.get(f"/projects/{project_id}/tags", headers=auth_headers)
    assert any(t["id"] == tag for t in tags.json())
