from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Multi-Agent AI Research System"
    environment: str = "development"
    database_url: str = Field(
        default="postgresql+asyncpg://research:research@postgres:5432/research"
    )
    redis_url: str = "redis://redis:6379/0"
    tavily_api_key: str | None = None
    openai_api_key: str | None = None
    pipeline_timeout_seconds: int = 120
    max_subtasks: int = 6
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()

