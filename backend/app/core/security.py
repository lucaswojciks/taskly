"""Security primitives: password hashing (bcrypt) and JWT access tokens.

Pure functions only — no HTTP, no database. See ``docs/specs/auth.md``.
"""

import datetime as dt
import uuid
from typing import Any

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

from app.core.config import settings

_ACCESS_TOKEN_TYPE = "access"
_TIMING_DUMMY_PASSWORD = "timing-attack-mitigation-placeholder"

_password_hash = PasswordHash((BcryptHasher(rounds=settings.bcrypt_rounds),))
# Precomputed once so ``verify_password_dummy`` costs the same as a real verify.
_DUMMY_HASH = _password_hash.hash(_TIMING_DUMMY_PASSWORD)


class TokenError(Exception):
    """A JWT could not be decoded or failed validation.

    Callers translate this into ``NotAuthenticatedError`` so that every failure
    mode (malformed, bad signature, expired, wrong type) looks identical to the
    client.
    """


def hash_password(plain_password: str) -> str:
    return _password_hash.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _password_hash.verify(plain_password, hashed_password)


def verify_password_dummy() -> None:
    """Verify against a throwaway hash.

    Called on the "user not found" login path so the response time is
    comparable to the "wrong password" path (see spec §4.3).
    """
    _password_hash.verify(_TIMING_DUMMY_PASSWORD, _DUMMY_HASH)


def create_access_token(subject: uuid.UUID) -> str:
    now = dt.datetime.now(dt.UTC)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": _ACCESS_TOKEN_TYPE,
        "iat": now,
        "exp": now + dt.timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> uuid.UUID:
    """Return the subject (user id) of a valid access token.

    Raises ``TokenError`` for any invalid token.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.InvalidTokenError as exc:
        raise TokenError(str(exc)) from exc

    if payload.get("type") != _ACCESS_TOKEN_TYPE:
        raise TokenError("unexpected token type")

    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise TokenError("missing subject claim")
    try:
        return uuid.UUID(subject)
    except ValueError as exc:
        raise TokenError("subject claim is not a valid id") from exc
