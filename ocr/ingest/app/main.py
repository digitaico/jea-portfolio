"""Application entry point and composition root.

Ingest + quality assessment service. It knows nothing about preprocessing —
that is a separate downstream service that reads the stored originals and their
quality metrics.

The only place that names concrete adapters and wires them in (DIP). New format
= register another decoder; new storage backend = swap the store. Routes and the
rest stay untouched (OCP).
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.adapters.decoder import ImageDecoder, PdfDecoder
from app.adapters.preprocess import (
    CropToDocument,
    Denoise,
    Deskew,
    Illumination,
    MetricDrivenPreprocessor,
    Resize,
)
from app.adapters.quality import OpenCvQualityAssessor
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
app.state.preprocessor = build_preprocessor(settings.max_image_dim)
app.state.store = FilesystemImageStore(settings.storage_dir)
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")
# QC only: serve stored originals so they can be reviewed in /qc.
app.mount("/files", StaticFiles(directory=str(settings.storage_dir)), name="files")
app.include_router(routes.router)
