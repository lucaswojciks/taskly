"""Domain exceptions and the central exception handler."""

from app.exceptions.domain import (
    ConflictError,
    DomainError,
    EmailAlreadyExistsError,
    PermissionDeniedError,
    ResourceNotFoundError,
    ValidationError,
)
from app.exceptions.handlers import register_exception_handlers

__all__ = [
    "ConflictError",
    "DomainError",
    "EmailAlreadyExistsError",
    "PermissionDeniedError",
    "ResourceNotFoundError",
    "ValidationError",
    "register_exception_handlers",
]
