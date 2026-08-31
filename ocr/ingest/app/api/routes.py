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


@router.post("/images", response_class=HTMLResponse)
async def receive_images(
    request: Request,
    files: list[UploadFile] = File(...),
    settings: Settings = Depends(get_settings),
) -> HTMLResponse:
    # Transport confirmation only: read each part to learn its true size, then
    # report back. Nothing is decoded or stored in Stage 1.
    received = []
    for file in files:
        data = await file.read()
        received.append(
            {
                "filename": file.filename or "unnamed",
                "content_type": file.content_type or "unknown",
                "size_bytes": len(data),
            }
        )

    return templates.TemplateResponse(
        request,
        "result.html",
        {"title": settings.app_title, "received": received},
    )
