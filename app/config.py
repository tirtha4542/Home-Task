"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "AI Chatbot Assessment"
    app_env: str = "development"
    debug: bool = Field(default=False, validation_alias="APP_DEBUG")
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    database_path: Path = Path("data/chat_memory.db")

    gemini_api_key: str = ""
    gemini_api_base_url: str = "https://generativelanguage.googleapis.com/v1beta/models"
    gemini_model: str = "gemini-2.5-flash"
    llm_timeout_seconds: float = 45.0
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    system_prompt: str = (
        "You are a helpful conversational assistant. Provide clear, concise, and context-aware replies."
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings object for the process."""

    return Settings()
