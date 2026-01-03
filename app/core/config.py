"""
Application configuration via environment variables.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    # External Services
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Feature Flags
    USE_MOCK_DATA: bool = True  # Use mock data instead of live yfinance

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

