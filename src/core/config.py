"""Configuration module for Narrative-Craft."""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    PORT: int = 8001
    HOST: str = "0.0.0.0"

    # Database
    POSTGRES_USER: str = "narrative"
    POSTGRES_PASSWORD: str = "narrative_secret"
    POSTGRES_DB: str = "narrative_craft"
    POSTGRES_PORT: int = 5434
    DATABASE_URL: str = "postgresql+asyncpg://narrative:narrative_secret@localhost:5434/narrative_craft"

    # Redis
    REDIS_PORT: int = 6380
    REDIS_URL: str = "redis://localhost:6380/0"

    # Qdrant
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333

    # LLM Provider
    LLM_PROVIDER: str = "minimax"
    LLM_PRIMARY_PROVIDER: str = "minimax"
    MINIMAX_API_KEY: Optional[str] = None
    MINIMAX_BASE_URL: str = "https://api.minimax.io/v1"
    MINIMAX_MODEL: str = "MiniMax-M3"
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    # Observability
    LANGFUSE_PUBLIC_KEY: Optional[str] = None
    LANGFUSE_SECRET_KEY: Optional[str] = None
    LANGFUSE_HOST: str = "http://localhost:3001"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
