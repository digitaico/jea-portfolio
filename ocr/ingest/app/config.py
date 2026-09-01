"""Application configuration. All values come from .env."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # app / server
    app_title: str
    max_upload_mb: int

    # decode
    pdf_dpi: int

    # preprocess
    max_image_dim: int

    # readability gate
    readability_min_sharpness: float
    readability_min_brightness: float
    readability_max_brightness: float
    readability_min_contrast: float
    ocr_max_illegible_ratio: float

    # storage
    storage_dir: Path

    # ocr
    gemini_api_key: SecretStr
    gemini_model: str
    gemini_max_retries: int
    gemini_timeout: float
    gemini_temperature: float
    gemini_max_output_tokens: int
    ocr_input: Literal["processed", "original"]
    ocr_language_hint: str
    ocr_transcription_prompt_file: Path
    ocr_extraction_prompt_file: Path
    ocr_areas_file: Path


@lru_cache
def get_settings() -> Settings:
    return Settings()
