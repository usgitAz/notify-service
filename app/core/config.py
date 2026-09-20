from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # App
    app_name: str = "Notification Service"
    debug: bool = True

    # Database
    database_url: str = ""
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_recycle: int = 3600  # 1hour


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
