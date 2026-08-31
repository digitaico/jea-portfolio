"""Stage 1 HTTP layer: serve the upload page and accept the upload.

Stage 1 is the UI + transport only. The POST here just confirms the files
arrived (name / type / size). Decoding, normalizing, storing and visualizing are
Stages 2-4 and are intentionally NOT done here.
"""

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import Settings, get_settings
from app.domain.errors import DecodeError
from app.domain.ports import PageDecoder

router = APIRouter()

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


@router.get("/", response_class=HTMLResponse)
async def upload_page(
    request: Request, settings: Settings = Depends(get_settings)
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "upload.html",
        {"title": settings.app_title, "max_upload_mb": settings.max_upload_mb},
    )


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/rootCA.pem")
async def root_ca() -> FileResponse:
    # Lets the phone download the mkcert CA to trust the LAN HTTPS cert.
    ca_path = Path(__file__).resolve().parent.parent.parent / "certs" / "rootCA.pem"
    if not ca_path.exists():
        raise HTTPException(status_code=404, detail="CA not generated yet.")
    return FileResponse(
        ca_path, media_type="application/x-x509-ca-cert", filename="rootCA.pem"
    )


def get_decoders(request: Request) -> list[PageDecoder]:
    # Injected at startup (composition root). Route never constructs decoders.
    return request.app.state.decoders


def _select_decoder(
    decoders: list[PageDecoder], filename: str, content_type: str | None
) -> PageDecoder | None:
    # OCP: first decoder that supports the file wins; adding a format = adding
    # a decoder in the composition root, not editing this loop.
    for decoder in decoders:
        if decoder.supports(filename, content_type):
            return decoder
    return None


@router.post("/images", response_class=HTMLResponse)
async def receive_images(
    request: Request,
    files: list[UploadFile] = File(...),
    settings: Settings = Depends(get_settings),
    decoders: list[PageDecoder] = Depends(get_decoders),
) -> HTMLResponse:
    # Stage 2: decode + normalize to RGB. Report decoded pages and metadata.
    # Per-file isolation: one bad file fails that file, not the batch.
    received = []
    for file in files:
        data = await file.read()
        filename = file.filename or "sin-nombre"
        decoder = _select_decoder(decoders, filename, file.content_type)

        if decoder is None:
            received.append({"filename": filename, "error": "Formato no soportado"})
            continue
        try:
            pages = decoder.decode(data, filename, file.content_type)
        except DecodeError as exc:
            received.append({"filename": filename, "error": str(exc)})
            continue

        first = pages[0]
        received.append(
            {
                "filename": filename,
                "source_format": first.source_format,
                "page_count": first.page_count,
                "size_bytes": len(data),
                "dimensions": f"{first.width}×{first.height}",
            }
        )

    return templates.TemplateResponse(
        request,
        "result.html",
        {"title": settings.app_title, "received": received},
    )
