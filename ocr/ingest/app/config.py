"""Application configuration. All values come from .env."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_title: str
    max_upload_mb: int
    pdf_dpi: int
    max_image_dim: int
    storage_dir: Path


@lru_cache
def get_settings() -> Settings:
    return Settings()
