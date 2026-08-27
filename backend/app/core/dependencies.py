"""Shared FastAPI dependencies.

Re-exports the database session dependency so routers depend on
``app.core.dependencies`` rather than reaching into ``app.db`` directly.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session

DbSession = Annotated[AsyncSession, Depends(get_session)]
