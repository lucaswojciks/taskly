"""Custom domain exceptions.

Services raise these instead of ``fastapi.HTTPException`` so the business layer
stays free of HTTP concerns. The mapping to HTTP status codes lives in one place:
``app.exceptions.handlers``.
"""


class DomainError(Exception):
    """Base class for all domain errors.

    ``code`` is a stable, machine-readable identifier returned in the error body.
    """

    code: str = "domain_error"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.__class__.__doc__ or "Domain error"
        super().__init__(self.message)


class ResourceNotFoundError(DomainError):
    """The requested resource does not exist."""

    code = "resource_not_found"


class ConflictError(DomainError):
    """The request conflicts with the current state of a resource."""

    code = "conflict"


class EmailAlreadyExistsError(ConflictError):
    """A user with this email address already exists."""

    code = "email_already_exists"


class PermissionDeniedError(DomainError):
    """The current principal is not allowed to perform this action."""

    code = "permission_denied"


class ValidationError(DomainError):
    """A business rule rejected the input."""

    code = "validation_error"


class AuthenticationError(DomainError):
    """Base class for authentication failures (maps to HTTP 401)."""

    code = "authentication_error"


class InvalidCredentialsError(AuthenticationError):
    """Invalid email or password."""

    code = "invalid_credentials"


class NotAuthenticatedError(AuthenticationError):
    """Not authenticated."""

    code = "not_authenticated"
