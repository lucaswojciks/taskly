"""Application configuration, loaded from environment / .env via Pydantic Settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the Taskly API."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Taskly API"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://taskly:taskly@localhost:5432/taskly"
    test_database_url: str = "postgresql+asyncpg://taskly:taskly@localhost:5432/taskly_test"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


settings = get_settings()
