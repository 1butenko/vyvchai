from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from pyparsing import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    APP_NAME: str = "Vyvchai"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    API_V1_PREFIX: str = "/api/v1"
    ALLOWED_HOSTS: List[str] = ["*"]
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8501"]

    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/mriia"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40
    DB_ECHO: bool = False

    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600

    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION: str = "textbook_chunks"

    LAPA_LLM_URL: str = "##LAPA_LLM_URL##"
    OPENAI_API_KEY: Optional[str] = None
    FALLBACK_TO_CLOUD: bool = False

    PHOENIX_ENABLED: bool = True
    PHOENIX_URL: str = "http://localhost:6006"

    DRAMATIQ_BROKER: str = "redis://localhost:6379/1"
    WORKER_CONCURRENCY: int = 4

    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000

    ENABLE_BENCHMARK_ENDPOINT: bool = True
    MAX_QUIZ_QUESTIONS: int = 12
    MAX_REGENERATION_ATTEMPTS: int = 3


@lru_cache()
def get_settings() -> Settings:
    return Settings()
