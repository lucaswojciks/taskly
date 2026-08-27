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

# Force the JWT signing secret to the value the auth tests use to forge tokens,
# so "expired token" exercises the expiry path and not the signature path.
# Must be set before app.core.config is imported.
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-auth-tests-not-for-production-use"

import uuid
from collections.abc import AsyncGenerator

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
