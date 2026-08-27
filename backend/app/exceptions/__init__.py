"""Domain exceptions and the central exception handler."""

from app.exceptions.domain import (
    AuthenticationError,
    ConflictError,
    DomainError,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    InvalidTagIdsError,
    NotAuthenticatedError,
    PermissionDeniedError,
    ResourceNotFoundError,
    ValidationError,
)
from app.exceptions.handlers import register_exception_handlers

__all__ = [
    "AuthenticationError",
    "ConflictError",
    "DomainError",
    "EmailAlreadyExistsError",
    "InvalidCredentialsError",
    "InvalidTagIdsError",
    "NotAuthenticatedError",
    "PermissionDeniedError",
    "ResourceNotFoundError",
    "ValidationError",
    "register_exception_handlers",
]
