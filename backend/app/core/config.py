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

    # Object storage (Cloudflare R2, S3-compatible). Like JWT_SECRET_KEY, the
    # credentials MUST be overridden in production; the defaults only let local
    # dev and the test suite import without extra setup (the tests stub storage).
    r2_account_id: str = "dev-account"
    r2_endpoint_url: str = "https://dev-account.r2.cloudflarestorage.com"
    r2_access_key_id: str = "dev-access-key-id"
    r2_secret_access_key: str = "dev-secret-access-key"
    r2_bucket: str = "taskly-attachments"

    attachment_max_bytes: int = 10 * 1024 * 1024
    attachment_url_ttl_seconds: int = 3600


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


settings = get_settings()
