"""Shared test fixtures.

Isolation strategy
------------------
* One engine per test session, pointed at ``TEST_DATABASE_URL``.
* Tables are created once at the start of the session and dropped at the end.
* Each test runs inside an outer transaction that is rolled back on teardown,
  so no test can see another test's writes.
* The HTTP client overrides the ``get_session`` dependency with the rolled-back
  session, so endpoints and assertions share the same transaction.
"""

import os

# These must be set before app.core.config is imported.
# JWT secret: match the value the auth tests use to forge tokens, so the
# "expired token" test exercises the expiry path and not the signature path.
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-auth-tests-not-for-production-use"
# Small attachment size limit so the "file too large" test stays cheap
# (keep TEST_ATTACHMENT_MAX_BYTES in tests/test_attachments.py in sync).
os.environ["ATTACHMENT_MAX_BYTES"] = "65536"

import importlib
import uuid
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app import models  # noqa: F401 - registers every model on Base.metadata
from app.core.config import settings
from app.db.base import Base
from app.db.session import get_session
from app.main import app
from tests.fake_storage import FakeStorage
from tests.helpers import Headers, NewUser


@pytest_asyncio.fixture(scope="session")
async def engine() -> AsyncGenerator[AsyncEngine]:
    async_engine = create_async_engine(settings.test_database_url, pool_pre_ping=True)
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield async_engine
    finally:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await async_engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession]:
    connection: AsyncConnection = await engine.connect()
    transaction = await connection.begin()
    session_factory = async_sessionmaker(bind=connection, expire_on_commit=False)
    session = session_factory()
    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback()
        await connection.close()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    async def _override_get_session() -> AsyncGenerator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _override_get_session
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as http_client:
            yield http_client
    finally:
        app.dependency_overrides.pop(get_session, None)


@pytest_asyncio.fixture
async def new_user(client: AsyncClient) -> NewUser:
    """Factory: register + log in a fresh user, return their Authorization header.

    Each call creates a distinct user, so tests that need to check per-user
    isolation can just call it twice.
    """

    async def _create(password: str = "s3cure-pass") -> Headers:
        email = f"user-{uuid.uuid4().hex[:12]}@example.com"
        registered = await client.post(
            "/auth/register", json={"email": email, "password": password}
        )
        assert registered.status_code == 201, registered.text
        logged_in = await client.post("/auth/login", json={"email": email, "password": password})
        assert logged_in.status_code == 200, logged_in.text
        token = logged_in.json()["access_token"]
        assert isinstance(token, str)
        return {"Authorization": f"Bearer {token}"}

    return _create


@pytest_asyncio.fixture
async def auth_headers(new_user: NewUser) -> Headers:
    """Authorization header for a single freshly-created user (the common case)."""
    return await new_user()


@pytest.fixture
def storage(client: AsyncClient) -> Generator[FakeStorage]:
    """Install an in-memory object-storage fake via a dependency override.

    Mirrors how ``client`` overrides ``get_session``. Until
    ``app.core.storage.get_storage`` exists (attachment feature not implemented
    yet) this is a no-op and the attachment tests fail on the missing routes.
    """
    fake = FakeStorage()
    try:
        storage_module = importlib.import_module("app.core.storage")
    except ImportError:
        yield fake
        return

    get_storage = vars(storage_module).get("get_storage")
    if get_storage is None:
        yield fake
        return

    app.dependency_overrides[get_storage] = lambda: fake
    try:
        yield fake
    finally:
        app.dependency_overrides.pop(get_storage, None)
