from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "FastAPI Blog API"
    app_env: Literal["dev", "test", "prod"] = "dev"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    database_url: str = "sqlite+aiosqlite:///./blog.db"
    auto_create_tables: bool = True

    secret_key: str = "replace-me-with-a-long-random-secret"
    access_token_expire_minutes: int = 60
    algorithm: str = "HS256"

    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

