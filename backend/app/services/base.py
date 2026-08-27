"""Base service.

Services hold the business rules. They orchestrate one or more repositories and
raise domain exceptions (see ``app.exceptions``) on rule violations. They know
nothing about HTTP (no request/response objects, no status codes) and nothing
about raw SQL.
"""

from sqlalchemy.ext.asyncio import AsyncSession


class BaseService:
    """Common wiring for services: holds the active async session."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
