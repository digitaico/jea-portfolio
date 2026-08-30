"""Application configuration.

DIP note: the rest of the app depends on this typed ``Settings`` object, never on
``os.environ`` scattered across modules. Every value comes from the environment
or the ``.env`` file — nothing is hardcoded.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed configuration parsed once from the environment / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_api_key: SecretStr
    gemini_model: str = "gemini-2.5-flash"
    pdf_dpi: int = 200
    max_image_dim: int = 2048
    max_upload_mb: int = 20
    output_dir: Path = Path("./output")


@lru_cache
def get_settings() -> Settings:
    """Cached accessor so the ``.env`` is parsed a single time per process."""
    return Settings()  # type: ignore[call-arg]
