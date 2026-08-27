"""Central mapping from domain exceptions to HTTP responses."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.exceptions.domain import (
    ConflictError,
    DomainError,
    PermissionDeniedError,
    ResourceNotFoundError,
    ValidationError,
)

_STATUS_BY_EXCEPTION: list[tuple[type[DomainError], int]] = [
    (ResourceNotFoundError, status.HTTP_404_NOT_FOUND),
    (PermissionDeniedError, status.HTTP_403_FORBIDDEN),
    (ConflictError, status.HTTP_409_CONFLICT),
    (ValidationError, 422),
]


def _status_for(exc: DomainError) -> int:
    for exc_type, http_status in _STATUS_BY_EXCEPTION:
        if isinstance(exc, exc_type):
            return http_status
    return status.HTTP_400_BAD_REQUEST


async def _domain_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, DomainError)  # narrowing for the type checker
    return JSONResponse(
        status_code=_status_for(exc),
        content={"error": {"code": exc.code, "message": exc.message}},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Wire the domain exception handler into the FastAPI app."""
    app.add_exception_handler(DomainError, _domain_error_handler)
