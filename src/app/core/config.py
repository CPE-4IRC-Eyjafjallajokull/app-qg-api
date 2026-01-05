from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseEnvSettings(BaseSettings):
    """Base settings that reads from .env with UTF-8 encoding."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class AppSettings(BaseEnvSettings):
    """Service-level settings (prefix: APP_)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="APP_",
    )

    version: str = "latest"
    name: str = "app-qg-api"
    debug: bool = False
    environment: str = "local"
    log_level: str = "INFO"
    log_format: str = "json"

    # CORS settings
    cors_origins: list[str] | str = ["*"]

    # SSE / events
    events_ping_interval_seconds: int = 25

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_commas(cls, value):
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in {"json", "console"}:
            msg = "log_format must be either 'json' or 'console'"
            raise ValueError(msg)
        return normalized


class DatabaseSettings(BaseEnvSettings):
    """Database configuration (prefix: POSTGRES_)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="POSTGRES_",
    )

    dsn: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/app"


class RabbitMQSettings(BaseEnvSettings):
    """RabbitMQ configuration (prefix: RABBITMQ_)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="RABBITMQ_",
    )

    dsn: str = "amqp://guest:guest@localhost:5672/"
    connect_timeout_seconds: float = 5.0


class AuthSettings(BaseEnvSettings):
    """Auth toggles (prefix: APP_AUTH_)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="AUTH_",
    )

    disabled: bool = False


class KeycloakSettings(BaseEnvSettings):
    """Keycloak configuration (prefix: KEYCLOAK_)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="KEYCLOAK_",
    )

    server_url: str = "http://localhost:8080"
    realm: str = "master"
    client_id: str = "app-qg-api"
    audience: str | None = None
    cache_ttl_seconds: int = 300
    timeout_seconds: float = 3.0
    jwks_url: str | None = None
    issuer: str | None = None

    def get_issuer(self) -> str:
        if self.issuer:
            return self.issuer
        return f"{self.server_url.rstrip('/')}/realms/{self.realm}"

    def get_jwks_url(self) -> str:
        if self.jwks_url:
            return self.jwks_url
        return f"{self.get_issuer()}/protocol/openid-connect/certs"


class NominatimSettings(BaseEnvSettings):
    """Nominatim reverse-geocoding configuration (prefix: NOMINATIM_)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="NOMINATIM_",
    )

    base_url: str = "https://nominatim.openstreetmap.org"
    timeout_seconds: float = 4.0
    user_agent: str | None = None
    accept_language: str = "fr"
    cache_ttl_seconds: float = 600.0
    throttle_seconds: float = 1.0
    cache_rounding_precision: int = 5


class Settings(BaseEnvSettings):
    """Root application settings grouped by concern."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app: AppSettings = Field(default_factory=AppSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    rabbitmq: RabbitMQSettings = Field(default_factory=RabbitMQSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    keycloak: KeycloakSettings = Field(default_factory=KeycloakSettings)
    nominatim: NominatimSettings = Field(default_factory=NominatimSettings)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
