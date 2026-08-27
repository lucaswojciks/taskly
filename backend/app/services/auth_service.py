"""Authentication business rules: registration and login.

Knows nothing about HTTP. Raises domain exceptions (never ``HTTPException``).
"""

from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
    verify_password_dummy,
)
from app.exceptions.domain import EmailAlreadyExistsError, InvalidCredentialsError
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, Token, UserCreate
from app.services.base import BaseService


def _normalize_email(email: str) -> str:
    return email.strip().lower()


class AuthService(BaseService):
    @property
    def _users(self) -> UserRepository:
        return UserRepository(self.session)

    async def register(self, data: UserCreate) -> User:
        email = _normalize_email(data.email)

        # Fast path: reject a known-duplicate before hashing the password.
        if await self._users.get_by_email(email) is not None:
            raise EmailAlreadyExistsError

        user = User(email=email, hashed_password=hash_password(data.password))
        self.session.add(user)
        try:
            # The UNIQUE constraint on users.email is the source of truth and
            # closes the race between the check above and this insert.
            await self.session.flush()
        except IntegrityError as exc:
            raise EmailAlreadyExistsError from exc

        await self.session.refresh(user)
        return user

    async def authenticate(self, data: LoginRequest) -> Token:
        email = _normalize_email(data.email)
        user = await self._users.get_by_email(email)

        if user is None:
            # Keep the timing comparable to the wrong-password path so the
            # response cannot be used to tell whether the email exists.
            verify_password_dummy()
            raise InvalidCredentialsError

        if not verify_password(data.password, user.hashed_password):
            raise InvalidCredentialsError

        return Token(
            access_token=create_access_token(user.id),
            expires_in=settings.access_token_expire_minutes * 60,
        )
