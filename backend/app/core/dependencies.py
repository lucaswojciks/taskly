"""Shared FastAPI dependencies.

Routers depend on this module rather than reaching into ``app.db``,
``app.core.security`` or the repositories directly.
"""

import uuid
from typing import Annotated, NamedTuple

from fastapi import Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import TokenError, decode_access_token
from app.db.session import get_session
from app.exceptions.domain import NotAuthenticatedError, ResourceNotFoundError
from app.models.project import Project
from app.models.user import User
from app.repositories.project import ProjectRepository
from app.repositories.user import UserRepository

DbSession = Annotated[AsyncSession, Depends(get_session)]

# auto_error=False: a missing/!Bearer header yields None here so we can raise our
# own domain error instead of FastAPI's default 403.
_bearer_scheme = HTTPBearer(auto_error=False)
_BearerCredentials = Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)]


async def get_current_user(session: DbSession, credentials: _BearerCredentials) -> User:
    """Resolve the authenticated user from the ``Authorization: Bearer`` token.

    Every failure mode (no token, malformed, bad signature, expired, unknown
    user) raises the same ``NotAuthenticatedError``.
    """
    if credentials is None:
        raise NotAuthenticatedError

    try:
        user_id = decode_access_token(credentials.credentials)
    except TokenError as exc:
        raise NotAuthenticatedError from exc

    user = await UserRepository(session).get_by_id(user_id)
    if user is None:
        raise NotAuthenticatedError
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_owned_project(
    project_id: uuid.UUID, session: DbSession, current_user: CurrentUser
) -> Project:
    """Resolve a project from the path, scoped to the current user.

    Returns 404 (never 403) when the project does not exist or belongs to
    someone else — see docs/specs/projects-tasks-tags.md §4.1. Reused by the
    project, task and tag routers.
    """
    project = await ProjectRepository(session).get_owned(project_id, current_user.id)
    if project is None:
        raise ResourceNotFoundError("Project not found.")
    return project


OwnedProject = Annotated[Project, Depends(get_owned_project)]


class Pagination(NamedTuple):
    limit: int
    offset: int


def pagination_params(
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Pagination:
    return Pagination(limit=limit, offset=offset)


PaginationParams = Annotated[Pagination, Depends(pagination_params)]
