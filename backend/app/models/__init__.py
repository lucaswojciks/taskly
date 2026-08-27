"""SQLAlchemy models package.

Import every model module here so that ``Base.metadata`` is fully populated
for Alembic autogenerate and for the test-suite table creation.
"""

from app.models.base import TimestampMixin, UUIDMixin

__all__ = ["TimestampMixin", "UUIDMixin"]
