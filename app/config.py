"""
Application Configuration Management for CloudSage.
Loads settings from environment variables and .env files.
"""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration model."""

    # Application Settings
    APP_NAME: str = "CloudSage"
    APP_ENV: str = "development"
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000
    DEBUG: bool = True
    APP_VERSION: str = "0.4.0"

    # AWS Configuration
    AWS_DEFAULT_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_SESSION_TOKEN: Optional[str] = None
    AWS_PROFILE: Optional[str] = None

    # Safe Development Mock Mode (True = uses realistic mock data for local testing)
    AWS_MOCK_MODE: bool = True

    # LLM Configuration
    LLM_PROVIDER: str = "openai"  # "openai", "gemini", or "local"
    LLM_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-4o-mini"

    # Storage & Database
    DATABASE_URL: str = "sqlite:///./data/cloudsage.db"
    VECTOR_STORE_PATH: str = "./data/vector_store"

    # Currency & Localization (INR)
    DEFAULT_CURRENCY: str = "INR"
    CURRENCY_SYMBOL: str = "₹"
    USD_TO_INR_RATE: float = 85.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
