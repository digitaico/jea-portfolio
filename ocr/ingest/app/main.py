"""Stage 1 application: FastAPI server with a Jinja2 upload page."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import routes
from app.config import get_settings

_STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title=get_settings().app_title)
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")
app.include_router(routes.router)
