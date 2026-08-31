"""HTTP layer. Thin on purpose (SRP): parse the request, enforce upload limits,
delegate to the pipeline, map domain errors to status codes. No image or OCR
logic lives here.
"""

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from app.config import Settings, get_settings
from app.domain.errors import UnsupportedFileError
from app.domain.models import DocumentResult
from app.domain.pipeline import ExtractionPipeline

router = APIRouter()


def get_pipeline(request: Request) -> ExtractionPipeline:
    """Return the singleton pipeline built once at startup (see lifespan).

    DIP at the edge: the route receives the pipeline; it never constructs
    concrete adapters itself.
    """
    return request.app.state.pipeline


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/extract", response_model=DocumentResult)
async def extract(
    file: UploadFile = File(...),
    pipeline: ExtractionPipeline = Depends(get_pipeline),
    settings: Settings = Depends(get_settings),
) -> DocumentResult:
    max_bytes = settings.max_upload_mb * 1024 * 1024

    # Early rejection when the client reports a size over the limit.
    if file.size is not None and file.size > max_bytes:
        raise HTTPException(status_code=413, detail="File too large.")

    data = await file.read()
    if len(data) > max_bytes:  # authoritative check after reading
        raise HTTPException(status_code=413, detail="File too large.")

    try:
        return await pipeline.run(
            data, file.filename or "upload", file.content_type
        )
    except UnsupportedFileError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
