"""
Centralized application configuration (spec §30).

Every environment variable the app reads is declared here, once. Nothing else in
the codebase should call ``os.getenv`` directly. Values are validated at startup
by pydantic-settings, so a misconfigured deployment fails fast and loudly instead
of halfway through a research run.
"""

from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---- environment ----
    environment: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # ---- security ----
    secret_key: str = Field(
        default="dev-insecure-secret-key-change-me-in-production-000000",
        description="HMAC key for signing JWTs. MUST be overridden in production.",
    )
    access_token_expire_minutes: int = 60 * 24
    jwt_algorithm: str = "HS256"

    # ---- database ----
    database_url: str = Field(
        default="sqlite:///./synthetic_research.db",
        description="SQLAlchemy URL. SQLite for local dev, PostgreSQL in docker-compose.",
    )

    # ---- CORS ----
    # NoDecode: read as a raw string from the env, split by the validator below,
    # rather than pydantic-settings trying to JSON-decode it.
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default=["http://localhost:5173", "http://localhost:3000"],
        description="Allowed browser origins for the SPA (comma-separated in the env).",
    )

    # ---- LLM provider ----
    # 'fake' returns deterministic structured data with NO network call — used by
    # tests and by reviewers who want to run the product without an API key.
    # 'openrouter' uses the real OpenRouter (OpenAI-compatible) API.
    llm_provider: Literal["openrouter", "fake"] = "fake"
    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    model_name: str | None = None
    fallback_model: str = "openrouter/free"
    llm_temperature_default: float = 0.7
    llm_max_tokens: int = 4096
    llm_timeout_seconds: int = 60
    llm_retries_per_model: int = 2
    llm_retry_backoff_seconds: float = 1.5
    app_referer: str = "http://localhost"
    app_title: str = "Synthetic User Research Platform"

    # ---- cost / abuse controls (spec §29) ----
    max_personas: int = 10
    min_personas: int = 2
    max_questions: int = 15
    min_questions: int = 3
    max_input_chars: int = 4000
    max_chat_message_chars: int = 2000

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, v):
        # Allow a comma-separated string from the environment.
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    """Cached accessor so settings are parsed once per process."""
    return Settings()


settings = get_settings()
