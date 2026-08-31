"""Stage 1 configuration, loaded from the environment / .env (nothing hardcoded)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed settings for the upload UI."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_title: str = "Document Image Upload"
    max_upload_mb: int = 20  # shown to the user; enforced properly in later stages


@lru_cache
def get_settings() -> Settings:
    """Parse the .env a single time per process."""
    return Settings()
