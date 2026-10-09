from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    database_url: str = "postgresql+psycopg://agentic_commerce:change-me@localhost:5432/agentic_commerce_support"
    cors_origins: list[str] = ["http://localhost:3000"]
    openai_api_key: str | None = None
    openai_chat_model: str = "gpt-4.1-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_embedding_dimensions: int = 1536

    model_config = SettingsConfigDict(
        env_file="../../.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

