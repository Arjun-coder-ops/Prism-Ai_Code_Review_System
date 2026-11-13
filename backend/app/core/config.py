from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed configuration safe for local foundation use."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "PRISM API"
    app_version: str = "0.1.0"
    app_env: str = Field(
        default="development",
        validation_alias=AliasChoices("APP_ENV", "PRISM_APP_ENV"),
    )
    database_url: str = Field(
        default="postgresql+asyncpg://prism:prism@localhost:5432/prism",
        validation_alias=AliasChoices("DATABASE_URL", "PRISM_DATABASE_URL"),
    )
    direct_database_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "DIRECT_DATABASE_URL",
            "PRISM_DIRECT_DATABASE_URL",
        ),
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        validation_alias=AliasChoices("REDIS_URL", "PRISM_REDIS_URL"),
    )
    database_pool_size: int = Field(
        default=5,
        ge=1,
        le=20,
        validation_alias=AliasChoices(
            "DATABASE_POOL_SIZE",
            "PRISM_DATABASE_POOL_SIZE",
        ),
    )
    database_connect_timeout: float = Field(
        default=10.0,
        gt=0,
        le=60,
        validation_alias=AliasChoices(
            "DATABASE_CONNECT_TIMEOUT",
            "PRISM_DATABASE_CONNECT_TIMEOUT",
        ),
    )
    llm_primary_provider: Literal["groq"] = "groq"
    llm_fallback_provider: Literal["gemini"] = "gemini"
    groq_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("GROQ_API_KEY", "PRISM_GROQ_API_KEY"),
    )
    gemini_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("GEMINI_API_KEY", "PRISM_GEMINI_API_KEY"),
    )
    groq_model: str = "openai/gpt-oss-20b"
    gemini_model: str = "gemini-3.5-flash"

    @property
    def migration_database_url(self) -> str:
        return self.direct_database_url or self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
