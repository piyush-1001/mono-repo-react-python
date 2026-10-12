"""Application configuration and environment settings."""

from enum import StrEnum

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnvironment(StrEnum):
    """Deployment environment the service is running in."""

    LOCAL = "local"
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Application settings loaded from the process environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- runtime ---
    APP_NAME: str = Field("inventory-api", alias="APP_NAME")
    APP_VERSION: str = Field("1.0.0", alias="APP_VERSION")
    ENV: AppEnvironment = Field(AppEnvironment.LOCAL, alias="ENV")
    DEBUG: bool = Field(False, alias="DEBUG")
    API_PREFIX: str = Field("/api", alias="API_PREFIX")
    ALLOWED_ORIGINS: str = Field("*", alias="ALLOWED_ORIGINS")
    WORKERS: int = Field(4, alias="WORKERS")
    TIMEOUT: int = Field(60, alias="TIMEOUT")

    # --- database ---
    DATABASE_ENGINE: str = Field("postgresql+asyncpg", alias="DATABASE_ENGINE")
    DATABASE_HOST: str | None = Field(None, alias="DATABASE_HOST")
    DATABASE_PORT: int | None = Field(5432, alias="DATABASE_PORT")
    DATABASE_USER: str | None = Field(None, alias="DATABASE_USER")
    DATABASE_PASSWORD: str | None = Field(None, alias="DATABASE_PASSWORD")
    DATABASE_NAME: str | None = Field(None, alias="DATABASE_NAME")
    DATABASE_URL: str | None = Field(None, alias="DATABASE_URL")
    DATABASE_ECHO: bool = Field(False, alias="DATABASE_ECHO")
    DATABASE_POOL_SIZE: int = Field(10, alias="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(20, alias="DATABASE_MAX_OVERFLOW")

    # --- redis ---
    REDIS_HOST: str | None = Field(None, alias="REDIS_HOST")
    REDIS_PORT: int | None = Field(6379, alias="REDIS_PORT")
    REDIS_DB: int = Field(0, alias="REDIS_DB")
    REDIS_PASSWORD: str | None = Field(None, alias="REDIS_PASSWORD")

    # --- security ---
    JWT_SECRET_KEY: str | None = Field(None, alias="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field("HS256", alias="JWT_ALGORITHM")
    ACCESS_TOKEN_LIFETIME: int = Field(60 * 30, alias="ACCESS_TOKEN_LIFETIME")
    REFRESH_TOKEN_LIFETIME: int = Field(60 * 60 * 24 * 7, alias="REFRESH_TOKEN_LIFETIME")
    RSA_PRIVATE_KEY: str | None = Field(None, alias="RSA_PRIVATE_KEY")
    RSA_PUBLIC_KEY: str | None = Field(None, alias="RSA_PUBLIC_KEY")
    DECRYPT_REQUEST_TIME_CHECK: bool | None = Field(True, alias="DECRYPT_REQUEST_TIME_CHECK")
    PASSWORD_MIN_LENGTH: int = Field(8, alias="PASSWORD_MIN_LENGTH")

    # --- cookies ---
    COOKIE_DOMAIN: str | None = Field(None, alias="COOKIE_DOMAIN")
    COOKIE_SECURE: bool = Field(False, alias="COOKIE_SECURE")
    COOKIE_SAMESITE: str = Field("lax", alias="COOKIE_SAMESITE")

    # --- rate limiting ---
    RATE_LIMIT_REQUESTS: int = Field(10, alias="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_WINDOW: int = Field(5, alias="RATE_LIMIT_WINDOW")

    # --- observability ---
    SENTRY_DSN: str | None = Field(None, alias="SENTRY_DSN")
    SENTRY_TRACES_SAMPLE_RATE: float = Field(0.1, alias="SENTRY_TRACES_SAMPLE_RATE")
    LOG_LEVEL: str = Field("INFO", alias="LOG_LEVEL")

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_database_url(cls, value: str | None, info) -> str | None:
        """Build the async DSN from the individual ``DATABASE_*`` fields.

        Args:
            value: Explicit ``DATABASE_URL`` when provided.
            info: Pydantic validation context exposing the sibling fields.

        Returns:
            The DSN to use, or ``None`` when it cannot be assembled.
        """
        if value:
            return value

        data = info.data
        host = data.get("DATABASE_HOST")
        user = data.get("DATABASE_USER")
        name = data.get("DATABASE_NAME")
        if not all((host, user, name)):
            return None

        password = data.get("DATABASE_PASSWORD")
        port = data.get("DATABASE_PORT") or 5432
        engine = data.get("DATABASE_ENGINE") or "postgresql+asyncpg"
        credentials = f"{user}:{password}" if password else user
        return f"{engine}://{credentials}@{host}:{port}/{name}"

    @field_validator("REDIS_HOST")
    @classmethod
    def normalize_redis_host(cls, value: str | None) -> str | None:
        """Trim whitespace introduced by copy-pasted environment files."""
        return value.strip() if value else value

    @model_validator(mode="after")
    def validate_required(self) -> "Settings":
        """Fail fast when a mandatory setting is missing in a deployed environment.

        Returns:
            The validated settings instance.

        Raises:
            ValueError: If a required setting is unset.
        """
        if self.ENV == AppEnvironment.LOCAL:
            return self

        required = {
            "DATABASE_URL": self.DATABASE_URL,
            "REDIS_HOST": self.REDIS_HOST,
            "JWT_SECRET_KEY": self.JWT_SECRET_KEY,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            msg = f"Missing required settings for {self.ENV}: {', '.join(missing)}"
            raise ValueError(msg)

        if len(self.JWT_SECRET_KEY or "") < 32:
            msg = "JWT_SECRET_KEY must be at least 32 characters outside local environment"
            raise ValueError(msg)

        return self

    @property
    def allowed_origins(self) -> list[str]:
        """CORS origins as a list."""
        if self.ALLOWED_ORIGINS.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def redis_url(self) -> str:
        """Redis connection URL derived from the individual settings."""
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT or 6379}/{self.REDIS_DB}"

    @property
    def is_production(self) -> bool:
        """Whether the service runs in production."""
        return self.ENV == AppEnvironment.PRODUCTION

    @property
    def is_staging(self) -> bool:
        """Whether the service runs in staging."""
        return self.ENV == AppEnvironment.STAGING

    @property
    def is_development(self) -> bool:
        """Whether the service runs in development."""
        return self.ENV == AppEnvironment.DEVELOPMENT

    @property
    def is_local(self) -> bool:
        """Whether the service runs locally."""
        return self.ENV == AppEnvironment.LOCAL


settings = Settings()
