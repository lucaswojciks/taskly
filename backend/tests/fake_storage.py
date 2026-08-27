"""In-memory fake for the object-storage backend, used by the attachment tests.

Substituted for the real R2-backed ``ObjectStorage`` via a FastAPI dependency
override (see the ``storage`` fixture in conftest). Never touches the network.
"""

import asyncio


class StorageFailure(RuntimeError):
    """Raised by the fake to simulate an R2 outage (network error / timeout)."""


class FakeStorage:
    """Records every call and keeps object bytes in a dict.

    Set ``fail_next_put`` / ``fail_next_delete`` to make the corresponding call
    raise ``StorageFailure``.
    """

    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.put_keys: list[str] = []
        self.delete_keys: list[str] = []
        self.fail_next_put = False
        self.fail_next_delete = False

    async def put_object(self, key: str, body: bytes, content_type: str) -> None:
        await asyncio.sleep(0)
        self.put_keys.append(key)
        if self.fail_next_put:
            raise StorageFailure("simulated R2 put failure")
        self.objects[key] = body

    async def delete_object(self, key: str) -> None:
        await asyncio.sleep(0)
        self.delete_keys.append(key)
        if self.fail_next_delete:
            raise StorageFailure("simulated R2 delete failure")
        self.objects.pop(key, None)

    def presigned_get_url(self, key: str) -> str:
        return f"https://fake-r2.test/{key}"
