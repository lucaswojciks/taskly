"""Object storage backend (Cloudflare R2, S3-compatible).

boto3 is blocking; ``put_object`` / ``delete_object`` run in a worker thread so
the event loop is not blocked. ``presigned_get_url`` is local signing (no I/O)
and stays synchronous. See docs/specs/attachments.md §4.6.
"""

from functools import lru_cache
from typing import Annotated, Any

import anyio.to_thread
import boto3
from botocore.config import Config
from fastapi import Depends

from app.core.config import settings


class ObjectStorage:
    """Thin async wrapper over a boto3 S3 client pointed at R2."""

    def __init__(self, *, client: Any, bucket: str, url_ttl_seconds: int) -> None:
        self._client = client
        self._bucket = bucket
        self._url_ttl_seconds = url_ttl_seconds

    async def put_object(self, key: str, body: bytes, content_type: str) -> None:
        def _call() -> None:
            self._client.put_object(
                Bucket=self._bucket, Key=key, Body=body, ContentType=content_type
            )

        await anyio.to_thread.run_sync(_call)

    async def delete_object(self, key: str) -> None:
        def _call() -> None:
            self._client.delete_object(Bucket=self._bucket, Key=key)

        await anyio.to_thread.run_sync(_call)

    def presigned_get_url(self, key: str) -> str:
        url = self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=self._url_ttl_seconds,
        )
        return str(url)


@lru_cache
def _default_storage() -> ObjectStorage:
    client = boto3.client(
        "s3",
        endpoint_url=settings.r2_endpoint_url,
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        region_name="auto",
        # Path-style addressing works with both Cloudflare R2 and a local
        # MinIO container (see docker-compose.yml).
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
        ),
    )
    return ObjectStorage(
        client=client,
        bucket=settings.r2_bucket,
        url_ttl_seconds=settings.attachment_url_ttl_seconds,
    )


def get_storage() -> ObjectStorage:
    """FastAPI dependency. Overridden in tests with an in-memory fake."""
    return _default_storage()


StorageDep = Annotated[ObjectStorage, Depends(get_storage)]
