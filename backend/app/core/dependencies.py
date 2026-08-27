"""Shared FastAPI dependencies.

Routers depend on this module rather than reaching into ``app.db`` or
``app.core.security`` directly.
"""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import TokenError, decode_access_token
from app.db.session import get_session
from app.exceptions.domain import NotAuthenticatedError
from app.models.user import User
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
