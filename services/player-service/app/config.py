from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from pydantic import Field, PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

SERVICE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ENV_FILE = SERVICE_ROOT / ".env"


class AppEnvironment(StrEnum):
    DEVELOPMENT = "development"  # For local development
    TEST = "test"  # To run tests
    PRODUCTION = "production"  # For deployed application


class Settings(BaseSettings):
    """Validated runtime settings.

    Process environment variables have priority over values from .env file.
    Production deployments therefore do not need to copy a local file into the
    container; the deployment platform can inject values directly.
    """

    model_config = SettingsConfigDict(
        env_file=DEFAULT_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        frozen=True,
    )

    app_env: AppEnvironment = Field(
        default=AppEnvironment.DEVELOPMENT,
        description="Application environment (development, test, production)",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode (e.g., detailed error pages, hot reload)",
    )

    http_host: str = Field(
        default="0.0.0.0",
        description="Host address for the HTTP server",
    )
    http_port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Port for the HTTP server",
    )
    grpc_host: str = Field(
        default="0.0.0.0",
        description="Host address for the gRPC server",
    )
    grpc_port: int = Field(
        default=50051,
        ge=1,
        le=65535,
        description="Port for the gRPC server",
    )

    postgres_user: str = Field(
        min_length=1,
        description="PostgreSQL user name",
    )
    postgres_password: SecretStr = Field(
        description="PostgreSQL password (kept secret)",
    )
    postgres_host: str = Field(
        min_length=1,
        description="PostgreSQL host address",
    )
    postgres_port: int = Field(
        default=5432,
        ge=1,
        le=65535,
        description="PostgreSQL port",
    )
    postgres_db: str = Field(
        min_length=1,
        description="PostgreSQL database name",
    )
    postgres_sql_echo: bool = Field(
        default=False,
        description="Log all SQL statements executed via SQLAlchemy",
    )

    log_level: str = Field(
        default="INFO",
        description="Logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    @property
    def database_url(self) -> PostgresDsn:
        """Build the async SQLAlchemy URL from validated PostgreSQL settings."""
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.postgres_user,
            password=self.postgres_password.get_secret_value(),
            host=self.postgres_host,
            port=self.postgres_port,
            path=self.postgres_db,
        )


def load_settings() -> Settings:
    """Load and validate settings without using the process-wide cache."""
    # noinspection PyArgumentList
    return Settings()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide immutable source of application settings."""
    return load_settings()
