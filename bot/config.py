"""Configuration management for the Discord Receipt Bot."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Discord
    discord_token: str
    discord_guild_id: int | None = None

    # Mistral OCR
    mistral_api_key: str
    mistral_ocr_model: str = "mistral-ocr-latest"
    ocr_table_format: str = "html"  # "html", "markdown", or None
    ocr_extract_header: bool = True
    ocr_use_structured_extraction: bool = True  # Enable/disable structured extraction

    # OpenRouter
    openrouter_api_key: str
    openrouter_model: str = "openai/gpt-4o-mini"

    # Google Sheets
    google_credentials_path: str = "credentials.json"
    google_spreadsheet_id: str

    # Application Settings
    confidence_threshold: float = 0.7
    data_dir: str = "data"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
