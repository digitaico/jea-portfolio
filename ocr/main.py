"""Application entry point and composition root.

This is the ONE place that imports concrete adapters and wires them together.
Everything above it (pipeline, ports, models) depends on abstractions only —
that separation is exactly what Dependency Injection buys us.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.adapters.gemini import GeminiFlashOcr
from app.adapters.loaders import ImageLoader, PdfLoader
from app.adapters.preprocess import OpenCvPreprocessor
from app.adapters.sinks import JsonTextSink
from app.api import routes
from app.config import get_settings
from app.domain.pipeline import ExtractionPipeline


def build_pipeline() -> ExtractionPipeline:
    """Construct the concrete adapters and inject them into the pipeline."""
    settings = get_settings()

    # OCP: register loaders in a list; new formats slot in here alone.
    loaders = [PdfLoader(settings.pdf_dpi), ImageLoader()]
    preprocessor = OpenCvPreprocessor(settings.max_image_dim)
    ocr = GeminiFlashOcr(
        api_key=settings.gemini_api_key.get_secret_value(),
        model_name=settings.gemini_model,
    )
    sink = JsonTextSink(settings.output_dir)

    return ExtractionPipeline(
        loaders=loaders,
        preprocessor=preprocessor,
        ocr=ocr,
        sink=sink,
        model_name=settings.gemini_model,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Build the Gemini client and pipeline once, then reuse across all requests.
    app.state.pipeline = build_pipeline()
    yield


app = FastAPI(title="Document Transcription Backend", lifespan=lifespan)
app.include_router(routes.router)
