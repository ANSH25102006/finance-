# ============================================================
#  config.py — Application settings loaded from .env
#  Uses Pydantic BaseSettings for type-safe configuration.
# ============================================================

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration. Values are loaded from the .env file
    in the backend directory (or from real environment variables)."""

    # --- Database ---
    database_url: str = "sqlite:///./dev.db"  # Override with PostgreSQL in .env

    # --- Security (placeholders — no auth implemented yet) ---
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # --- App meta ---
    app_name: str = "Personal Finance Spend Auditor"
    app_version: str = "0.1.0"
    debug: bool = True

    # --- AI Settings ---
    ai_provider: str = "mock"
    ai_model: str = "gpt-4o"
    ai_temperature: float = 0.0
    ai_max_tokens: int = 1000
    ai_timeout: float = 30.0
    ai_retry_count: int = 3
    ai_retry_backoff: float = 2.0

    # OpenAI specific settings
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_temperature: float = 0.0
    openai_max_tokens: int = 1000
    openai_timeout: float = 30.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Return a cached Settings instance.
    Use this via FastAPI dependency injection: Depends(get_settings)."""
    return Settings()
