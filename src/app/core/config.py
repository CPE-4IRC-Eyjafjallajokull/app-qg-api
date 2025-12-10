from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", env_prefix="APP_"
    )

    version: str = "latest"
    name: str = "app-qg-api"
    debug: bool = False
    environment: str = "local"
    log_level: str = "INFO"

    postgres_dsn: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/app"
    rabbitmq_dsn: str = "amqp://guest:guest@localhost:5672/"

    # CORS settings
    cors_origins: list[str] = ["*"]

    events_ping_interval_seconds: int = 25


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
