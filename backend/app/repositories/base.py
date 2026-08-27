"""Base repository.

Repositories own all data access: they build and run SQLAlchemy queries and
return models. They must not contain business rules — that belongs in services.
"""

from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    """Common wiring for repositories: holds the active async session."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
