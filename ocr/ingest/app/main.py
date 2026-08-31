"""Application entry point and composition root.

The only place that names concrete decoders and wires them in (DIP). New format
= register another decoder here; routes and the rest stay untouched (OCP).
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.adapters.decoder import ImageDecoder, PdfDecoder
from app.api import routes
from app.config import get_settings

_STATIC_DIR = Path(__file__).resolve().parent / "static"


def build_decoders():
    """Ordered list of decoders; the router picks the first that supports a file."""
    settings = get_settings()
    return [PdfDecoder(settings.pdf_dpi), ImageDecoder()]


app = FastAPI(title=get_settings().app_title)
app.state.decoders = build_decoders()
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")
app.include_router(routes.router)
