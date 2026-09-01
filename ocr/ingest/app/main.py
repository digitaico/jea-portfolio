"""Application entry point and composition root.

Ingest + quality assessment service. It knows nothing about preprocessing —
that is a separate downstream service that reads the stored originals and their
quality metrics.

The only place that names concrete adapters and wires them in (DIP). New format
= register another decoder; new storage backend = swap the store. Routes and the
rest stay untouched (OCP).
"""

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.adapters.decoder import ImageDecoder, PdfDecoder
from app.adapters.ocr import GeminiExtractor, GeminiOcr
from app.adapters.preprocess import (
    CropToDocument,
    Denoise,
    Deskew,
    Illumination,
    MetricDrivenPreprocessor,
    Resize,
)
from app.adapters.quality import OpenCvQualityAssessor
from app.adapters.readability import OcrTranscriptionGate, ThresholdReadabilityGate
from app.adapters.storage import FilesystemImageStore
from app.api import routes
from app.config import get_settings

_STATIC_DIR = Path(__file__).resolve().parent / "static"


def build_decoders():
    """Ordered list of decoders; the router picks the first that supports a file."""
    settings = get_settings()
    return [PdfDecoder(settings.pdf_dpi), ImageDecoder()]


def build_preprocessor(max_dim: int) -> MetricDrivenPreprocessor:
    """Ordered, metric-gated steps. Reorder/add/remove here only (OCP).
    No orientation step by design.
    """
    steps = [CropToDocument(), Deskew(), Illumination(), Denoise(), Resize(max_dim)]
    return MetricDrivenPreprocessor(steps)


settings = get_settings()

app = FastAPI(title=settings.app_title)
app.state.decoders = build_decoders()
app.state.assessor = OpenCvQualityAssessor()
app.state.gate = ThresholdReadabilityGate(
    min_sharpness=settings.readability_min_sharpness,
    min_brightness=settings.readability_min_brightness,
    max_brightness=settings.readability_max_brightness,
    min_contrast=settings.readability_min_contrast,
)
app.state.transcription_gate = OcrTranscriptionGate(
    max_illegible_ratio=settings.ocr_max_illegible_ratio,
)
app.state.preprocessor = build_preprocessor(settings.max_image_dim)
app.state.store = FilesystemImageStore(settings.storage_dir)

# Prompts and semantic areas are file-driven (paths from .env).
_transcription_prompt = settings.ocr_transcription_prompt_file.read_text(encoding="utf-8")
_extraction_prompt = settings.ocr_extraction_prompt_file.read_text(encoding="utf-8")
_areas = json.loads(settings.ocr_areas_file.read_text(encoding="utf-8"))

app.state.ocr = GeminiOcr(
    api_key=settings.gemini_api_key.get_secret_value(),
    model=settings.gemini_model,
    temperature=settings.gemini_temperature,
    max_output_tokens=settings.gemini_max_output_tokens,
    timeout=settings.gemini_timeout,
    max_retries=settings.gemini_max_retries,
    prompt_template=_transcription_prompt,
    language_hint=settings.ocr_language_hint,
)
app.state.extractor = GeminiExtractor(
    api_key=settings.gemini_api_key.get_secret_value(),
    model=settings.gemini_model,
    temperature=settings.gemini_temperature,
    max_output_tokens=settings.gemini_max_output_tokens,
    timeout=settings.gemini_timeout,
    max_retries=settings.gemini_max_retries,
    prompt_template=_extraction_prompt,
    language_hint=settings.ocr_language_hint,
    areas=_areas,
)
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")
# QC only: serve stored originals so they can be reviewed in /qc.
app.mount("/files", StaticFiles(directory=str(settings.storage_dir)), name="files")
app.include_router(routes.router)
