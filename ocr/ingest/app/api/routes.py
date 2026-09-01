"""Stage 1 HTTP layer: serve the upload page and accept the upload.

Stage 1 is the UI + transport only. The POST here just confirms the files
arrived (name / type / size). Decoding, normalizing, storing and visualizing are
Stages 2-4 and are intentionally NOT done here.
"""

import json
import uuid
from dataclasses import replace
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from app.adapters.render import to_data_uri
from app.config import Settings, get_settings
from app.domain.errors import DecodeError
from app.domain.ports import ImageStore, PageDecoder, Preprocessor, QualityAssessor

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


@router.get("/qc", response_class=HTMLResponse)
async def qc(
    request: Request, settings: Settings = Depends(get_settings)
) -> HTMLResponse:
    # QC view (evaluation, not end users): decoded originals + quality metrics.
    storage = settings.storage_dir
    grouped: dict[str, list[dict]] = {}
    if storage.exists():
        originals = sorted(
            storage.glob("*_original.png"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,  # most recent uploads first
        )
        for path in originals:
            base = path.name[: -len("_original.png")]   # <id>_p<N>
            image_id, _, page = base.partition("_p")
            quality_file = storage / f"{base}_quality.json"
            processed = storage / f"{base}_processed.png"
            report = storage / f"{base}_report.json"
            quality = None
            if quality_file.exists():
                try:
                    quality = json.loads(quality_file.read_text(encoding="utf-8"))
                except (ValueError, OSError):
                    quality = None
            notes = []
            if report.exists():
                try:
                    notes = json.loads(report.read_text(encoding="utf-8")).get("notes", [])
                except (ValueError, OSError):
                    notes = []
            grouped.setdefault(image_id, []).append(
                {
                    "page": int(page) if page.isdigit() else 0,
                    "original_url": f"/files/{path.name}",
                    "processed_url": f"/files/{base}_processed.png" if processed.exists() else None,
                    "quality": quality,
                    "notes": notes,
                }
            )

    docs = [
        {"image_id": image_id, "pages": sorted(pages, key=lambda x: x["page"])}
        for image_id, pages in grouped.items()
    ]
    return templates.TemplateResponse(
        request, "qc.html", {"title": settings.app_title, "docs": docs}
    )


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


def get_store(request: Request) -> ImageStore:
    return request.app.state.store


def get_assessor(request: Request) -> QualityAssessor:
    return request.app.state.assessor


def get_preprocessor(request: Request) -> Preprocessor:
    return request.app.state.preprocessor


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
    files: list[UploadFile] = File(default=[]),
    settings: Settings = Depends(get_settings),
    decoders: list[PageDecoder] = Depends(get_decoders),
    assessor: QualityAssessor = Depends(get_assessor),
    preprocessor: Preprocessor = Depends(get_preprocessor),
    store: ImageStore = Depends(get_store),
) -> HTMLResponse:
    # Ingest + assessment: decode -> normalize to RGB -> assess quality -> store
    # the original. Preprocessing is a separate downstream service; this one
    # knows nothing about it.
    # Per-file isolation: one bad file fails that file, not the batch.
    received = []

    # Guard: an empty form submission (no pick/capture) still sends a part with
    # a blank filename. Drop those; if nothing real remains, reject cleanly.
    usable = [f for f in files if (f.filename or "").strip()]
    if not usable:
        return templates.TemplateResponse(
            request,
            "result.html",
            {
                "title": settings.app_title,
                "received": [{"filename": "—", "error": "No seleccionaste ninguna imagen."}],
            },
        )

    for file in usable:
        data = await file.read()
        filename = file.filename or "sin-nombre"

        if not data:  # zero-byte part
            received.append({"filename": filename, "error": "Archivo vacío"})
            continue

        decoder = _select_decoder(decoders, filename, file.content_type)

        if decoder is None:
            received.append({"filename": filename, "error": "Formato no soportado"})
            continue
        try:
            pages = decoder.decode(data, filename, file.content_type)
        except DecodeError as exc:
            received.append({"filename": filename, "error": str(exc)})
            continue

        # One id per uploaded file; pages share it.
        image_id = uuid.uuid4().hex
        page_views = []
        for page in pages:
            # Assess quality on the decoded original, then automatically
            # preprocess by consuming those metrics. Store both + reports.
            page = replace(page, quality=assessor.assess(page))   # Stage 3
            store.save(image_id, page)                            # original + quality
            processed = preprocessor.process(page)                # Stage 4 (consumes metrics)
            store.save_processed(image_id, processed)             # processed + report
            page_views.append(                                    # show original to user
                {"index": page.page_index, "data_uri": to_data_uri(page)}
            )

        first = pages[0]
        received.append(
            {
                "filename": filename,
                "image_id": image_id,
                "source_format": first.source_format,
                "page_count": first.page_count,
                "size_bytes": len(data),
                "dimensions": f"{first.width}×{first.height}",
                "pages": page_views,
            }
        )

    return templates.TemplateResponse(
        request,
        "result.html",
        {"title": settings.app_title, "received": received},
    )
