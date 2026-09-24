from functools import lru_cache

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "Notification Service"
    app_description: str = (
        "super fast, fully non-blocking notification as a service - Nass"
    )
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    postgres_user: str = Field(..., description="PostgreSQL username")
    postgres_password: str = Field(..., description="PostgreSQL password")
    postgres_db: str = Field(..., description="PostgreSQL database name")
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # Connection pool tuning
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_recycle: int = 3600  # 1 hour

    # logging
    log_sample_rate: float = Field(
        le=1.0,
        ge=0.0,
        description="Sampling rate for access logs (0.0-1.0)",
        default=1.0,
    )
    log_skip_paths: list[str] = [  # endpoints excluded from access logs
        "/health",
        "/health/ready",
        "/docs",
        "/redoc",
        "/openapi.json",
    ]
    log_redact_headers: list[str] = [  # sensitive headers to mask (pii/security)
        "authorization",
        "cookie",
        "x-api-key",
        "x-auth-token",
    ]

    # uvicorn
    uvicorn_host: str = "0.0.0.0"
    uvicorn_port: int = 8000
    uvicorn_workers: int = 4

    # create database url
    @computed_field
    @property
    def database_url(self) -> str:
        """Async SQLAlchemy URL built from the individual DB settings."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
