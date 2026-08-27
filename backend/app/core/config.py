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

    # Authentication. In production JWT_SECRET_KEY MUST be overridden with a
    # random value of at least 32 bytes; the default here exists only so local
    # dev and the test suite run without extra setup.
    jwt_secret_key: str = "insecure-dev-secret-change-me-0123456789abcdef"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    bcrypt_rounds: int = 12


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


settings = get_settings()
