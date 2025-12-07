from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", env_prefix="APP_"
    )

    app_name: str = "app-qg-api"
    debug: bool = False
    environment: str = "local"
    log_level: str = "INFO"

    mongo_dsn: str = "mongodb://localhost:27017/app"
    postgres_dsn: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/app"
    rabbitmq_dsn: str = "amqp://guest:guest@localhost:5672/"

    events_ping_interval_seconds: int = 25


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
