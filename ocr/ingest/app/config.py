"""Stage 1 configuration, loaded from the environment / .env (nothing hardcoded)."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# config.py lives at ingest/app/config.py -> parent is app/
_APP_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    """Typed settings for the upload UI."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_title: str = "Lector de Órdenes Médicas"
    max_upload_mb: int = 20  # shown to the user; enforced properly in later stages
    pdf_dpi: int = 200       # rasterization DPI for PDF pages (Stage 2)
    storage_dir: Path = _APP_DIR / "storage"  # ingest/app/storage (override via .env)
    max_image_dim: int = 2000  # preprocessing resize cap (Stage 4)


@lru_cache
def get_settings() -> Settings:
    """Parse the .env a single time per process."""
    return Settings()
