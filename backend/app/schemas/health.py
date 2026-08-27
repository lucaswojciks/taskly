"""Schemas for the healthcheck endpoint."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Payload returned by ``GET /health``."""

    status: str = "ok"
