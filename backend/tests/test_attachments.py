"""Integration tests for Attachment endpoints.

Spec: ``docs/specs/attachments.md``. Written before the implementation exists:
the ``/projects/{id}/tasks/{task_id}/attachments`` routes are not registered
yet, so every test fails with 404 (route missing) or at a setup helper.

Object storage is a fake (``tests/fake_storage.py``) injected via a FastAPI
dependency override — no real R2, no network.
"""

from typing import Any

from httpx import AsyncClient, Response

from tests.fake_storage import FakeStorage
from tests.helpers import Headers, NewUser, create_project_id, create_task_id

# Keep in sync with ATTACHMENT_MAX_BYTES set in conftest for the test env.
TEST_ATTACHMENT_MAX_BYTES = 64 * 1024

# Minimal payloads carrying the right leading "magic bytes".
JPEG_BYTES = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00" + b"\x00" * 48
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 48
PDF_BYTES = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"
TEXT_BYTES = b"just plain text, definitely not an image or a pdf\n"


def assert_domain_error(response: Response, status: int, code: str) -> None:
    assert response.status_code == status, response.text
    body = response.json()
    assert "error" in body, f"expected a domain-error body, got: {body}"
    assert body["error"]["code"] == code


async def make_project_and_task(client: AsyncClient, headers: Headers) -> tuple[str, str]:
    project_id = await create_project_id(client, headers)
    task_id = await create_task_id(client, headers, project_id)
    return project_id, task_id


async def upload_attachment(
    client: AsyncClient,
    headers: Headers,
    project_id: str,
    task_id: str,
    *,
    content: bytes = JPEG_BYTES,
    filename: str = "photo.jpg",
    content_type: str = "image/jpeg",
) -> Response:
    return await client.post(
        f"/projects/{project_id}/tasks/{task_id}/attachments",
        files={"file": (filename, content, content_type)},
        headers=headers,
    )


async def upload_attachment_id(
    client: AsyncClient, headers: Headers, project_id: str, task_id: str, **kwargs: Any
) -> str:
    response = await upload_attachment(client, headers, project_id, task_id, **kwargs)
    assert response.status_code == 201, (
        f"setup: upload expected 201, got {response.status_code}: {response.text}"
    )
    attachment_id = response.json()["id"]
    assert isinstance(attachment_id, str)
    return attachment_id


# --------------------------------------------------------------------------- #
# upload
# --------------------------------------------------------------------------- #
async def test_upload_valid_jpeg_returns_201_with_url(
    client: AsyncClient, auth_headers: Headers, storage: FakeStorage
) -> None:
    project_id, task_id = await make_project_and_task(client, auth_headers)

    response = await upload_attachment(
        client, auth_headers, project_id, task_id, content=JPEG_BYTES, filename="photo.jpg"
    )

    assert response.status_code == 201
    body = response.json()
    assert body["content_type"] == "image/jpeg"
    assert body["file_name"] == "photo.jpg"
    assert "id" in body
    assert "uploaded_at" in body
    assert body["url"].startswith("https://fake-r2.test/")
    assert len(storage.put_keys) == 1


async def test_upload_valid_pdf_returns_201(
    client: AsyncClient, auth_headers: Headers, storage: FakeStorage
) -> None:
    project_id, task_id = await make_project_and_task(client, auth_headers)

    response = await upload_attachment(
        client,
        auth_headers,
        project_id,
        task_id,
        content=PDF_BYTES,
        filename="report.pdf",
        content_type="application/pdf",
    )

    assert response.status_code == 201
    assert response.json()["content_type"] == "application/pdf"


async def test_upload_disguised_text_file_returns_422(
    client: AsyncClient, auth_headers: Headers, storage: FakeStorage
) -> None:
    project_id, task_id = await make_project_and_task(client, auth_headers)

    # a text file with a forged image/png content-type and a .png name;
    # magic-byte validation must reject it
    response = await upload_attachment(
        client,
        auth_headers,
        project_id,
        task_id,
        content=TEXT_BYTES,
        filename="notes.png",
        content_type="image/png",
    )

    assert_domain_error(response, 422, "unsupported_file_type")
    assert storage.put_keys == []


async def test_upload_over_size_limit_returns_413(
    client: AsyncClient, auth_headers: Headers, storage: FakeStorage
) -> None:
    project_id, task_id = await make_project_and_task(client, auth_headers)
    oversized = JPEG_BYTES + b"\x00" * TEST_ATTACHMENT_MAX_BYTES

    response = await upload_attachment(
        client, auth_headers, project_id, task_id, content=oversized, filename="big.jpg"
    )

    assert_domain_error(response, 413, "file_too_large")
    assert storage.put_keys == []


async def test_upload_without_file_returns_422(
    client: AsyncClient, auth_headers: Headers, storage: FakeStorage
) -> None:
    project_id, task_id = await make_project_and_task(client, auth_headers)

    response = await client.post(
        f"/projects/{project_id}/tasks/{task_id}/attachments", headers=auth_headers
    )

    assert response.status_code == 422


async def test_upload_to_other_users_task_returns_404(
    client: AsyncClient, new_user: NewUser, storage: FakeStorage
) -> None:
    alice = await new_user()
    bob = await new_user()
    project_id, task_id = await make_project_and_task(client, alice)

    response = await upload_attachment(client, bob, project_id, task_id)

    assert_domain_error(response, 404, "resource_not_found")
    assert storage.put_keys == []


async def test_upload_storage_failure_returns_502_and_persists_nothing(
    client: AsyncClient, auth_headers: Headers, storage: FakeStorage
) -> None:
    project_id, task_id = await make_project_and_task(client, auth_headers)
    storage.fail_next_put = True

    response = await upload_attachment(client, auth_headers, project_id, task_id)

    assert_domain_error(response, 502, "storage_error")

    task = await client.get(f"/projects/{project_id}/tasks/{task_id}", headers=auth_headers)
    assert task.status_code == 200
    assert task.json()["attachments"] == []


# --------------------------------------------------------------------------- #
# delete
# --------------------------------------------------------------------------- #
async def test_delete_attachment_returns_204(
    client: AsyncClient, auth_headers: Headers, storage: FakeStorage
) -> None:
    project_id, task_id = await make_project_and_task(client, auth_headers)
    attachment_id = await upload_attachment_id(client, auth_headers, project_id, task_id)

    response = await client.delete(
        f"/projects/{project_id}/tasks/{task_id}/attachments/{attachment_id}",
        headers=auth_headers,
    )

    assert response.status_code == 204

    task = await client.get(f"/projects/{project_id}/tasks/{task_id}", headers=auth_headers)
    assert task.json()["attachments"] == []


async def test_delete_already_deleted_attachment_returns_404(
    client: AsyncClient, auth_headers: Headers, storage: FakeStorage
) -> None:
    project_id, task_id = await make_project_and_task(client, auth_headers)
    attachment_id = await upload_attachment_id(client, auth_headers, project_id, task_id)
    path = f"/projects/{project_id}/tasks/{task_id}/attachments/{attachment_id}"

    first = await client.delete(path, headers=auth_headers)
    assert first.status_code == 204

    second = await client.delete(path, headers=auth_headers)
    assert_domain_error(second, 404, "resource_not_found")


async def test_delete_attachment_of_other_users_task_returns_404(
    client: AsyncClient, new_user: NewUser, storage: FakeStorage
) -> None:
    alice = await new_user()
    bob = await new_user()
    project_id, task_id = await make_project_and_task(client, alice)
    attachment_id = await upload_attachment_id(client, alice, project_id, task_id)

    response = await client.delete(
        f"/projects/{project_id}/tasks/{task_id}/attachments/{attachment_id}",
        headers=bob,
    )

    assert_domain_error(response, 404, "resource_not_found")


async def test_delete_storage_failure_still_removes_db_record(
    client: AsyncClient, auth_headers: Headers, storage: FakeStorage
) -> None:
    project_id, task_id = await make_project_and_task(client, auth_headers)
    attachment_id = await upload_attachment_id(client, auth_headers, project_id, task_id)
    storage.fail_next_delete = True

    response = await client.delete(
        f"/projects/{project_id}/tasks/{task_id}/attachments/{attachment_id}",
        headers=auth_headers,
    )

    # best-effort: the R2 delete failed but the DB row is gone -> still 204
    assert response.status_code == 204

    task = await client.get(f"/projects/{project_id}/tasks/{task_id}", headers=auth_headers)
    assert task.json()["attachments"] == []


# --------------------------------------------------------------------------- #
# task detail embeds attachments
# --------------------------------------------------------------------------- #
async def test_task_detail_includes_attachments_with_url(
    client: AsyncClient, auth_headers: Headers, storage: FakeStorage
) -> None:
    project_id, task_id = await make_project_and_task(client, auth_headers)
    await upload_attachment_id(client, auth_headers, project_id, task_id, filename="a.jpg")
    await upload_attachment_id(
        client,
        auth_headers,
        project_id,
        task_id,
        content=PNG_BYTES,
        filename="b.png",
        content_type="image/png",
    )

    response = await client.get(f"/projects/{project_id}/tasks/{task_id}", headers=auth_headers)

    assert response.status_code == 200
    attachments = response.json()["attachments"]
    assert len(attachments) == 2
    for attachment in attachments:
        assert attachment["url"].startswith("https://fake-r2.test/")
        assert "id" in attachment
        assert "file_name" in attachment
        assert "content_type" in attachment
        assert "uploaded_at" in attachment
