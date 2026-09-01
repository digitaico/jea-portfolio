"""Stage 1 HTTP layer: serve the upload page and accept the upload.

Stage 1 is the UI + transport only. The POST here just confirms the files
arrived (name / type / size). Decoding, normalizing, storing and visualizing are
Stages 2-4 and are intentionally NOT done here.
"""

import asyncio
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
from app.domain.ports import (
    ImageStore,
    OcrProvider,
    PageDecoder,
    Preprocessor,
    QualityAssessor,
    ReadabilityGate,
    StructuredExtractor,
    TranscriptionGate,
)

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
    # QC view (evaluation, not end users): one folder per upload (its UUID).
    storage = settings.storage_dir
    docs = []
    if storage.exists():
        folders = [d for d in storage.iterdir() if d.is_dir()]
        folders.sort(key=lambda d: d.stat().st_mtime, reverse=True)  # recent first
        for folder in folders:
            image_id = folder.name
            pages = []
            for orig in folder.glob("p*_original.png"):
                base = orig.name[: -len("_original.png")]   # p<N>
                page_num = int(base[1:]) if base[1:].isdigit() else 0
                quality_file = folder / f"{base}_quality.json"
                report = folder / f"{base}_report.json"
                ocr_json = folder / f"{base}.json"
                processed = folder / f"{base}_processed.png"

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
                text = None
                if ocr_json.exists():
                    try:
                        text = json.loads(ocr_json.read_text(encoding="utf-8")).get("text")
                    except (ValueError, OSError):
                        text = None
                pages.append(
                    {
                        "page": page_num,
                        "original_url": f"/files/{image_id}/{orig.name}",
                        "processed_url": f"/files/{image_id}/{base}_processed.png" if processed.exists() else None,
                        "quality": quality,
                        "notes": notes,
                        "text": text,
                    }
                )
            pages.sort(key=lambda x: x["page"])
            if pages:
                docs.append({"image_id": image_id, "pages": pages})

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


def get_gate(request: Request) -> ReadabilityGate:
    return request.app.state.gate


def get_transcription_gate(request: Request) -> TranscriptionGate:
    return request.app.state.transcription_gate


def get_preprocessor(request: Request) -> Preprocessor:
    return request.app.state.preprocessor


def get_ocr(request: Request) -> OcrProvider:
    return request.app.state.ocr


def get_extractor(request: Request) -> StructuredExtractor:
    return request.app.state.extractor


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
    gate: ReadabilityGate = Depends(get_gate),
    preprocessor: Preprocessor = Depends(get_preprocessor),
    ocr: OcrProvider = Depends(get_ocr),
    extractor: StructuredExtractor = Depends(get_extractor),
    transcription_gate: TranscriptionGate = Depends(get_transcription_gate),
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
            # Assess quality, then gate on readability BEFORE anything is stored.
            page = replace(page, quality=assessor.assess(page))   # Stage 3
            verdict = gate.evaluate(page.quality)
            if not verdict.readable:
                # Not readable: nothing stored, no preprocessing, no OCR. Ask
                # the user for a better image; show the preview + the reasons.
                page_views.append(
                    {
                        "index": page.page_index,
                        "data_uri": to_data_uri(page),
                        "rejected": True,
                        "reasons": verdict.reasons,
                    }
                )
                continue

            store.save(image_id, page)                            # original + quality
            processed = preprocessor.process(page)                # Stage 4 (consumes metrics)
            store.save_processed(image_id, processed)             # processed + report

            # Stage 6: OCR the page chosen by OCR_INPUT (default: processed).
            source = settings.ocr_input
            ocr_page = processed if source == "processed" else page

            # Both model calls run concurrently (independent); failures isolated.
            text_res, struct_res = await asyncio.gather(
                ocr.transcribe(ocr_page),
                extractor.extract(ocr_page),
                return_exceptions=True,
            )
            if isinstance(text_res, Exception):
                page_text = f"[error de OCR: {text_res}]"
            else:
                page_text = text_res

            # OCR-output readability: the model is the real judge. If it read
            # nothing / mostly illegible, remove the stored files and ask again.
            ocr_verdict = transcription_gate.evaluate(page_text)
            if not ocr_verdict.readable:
                store.remove_page(image_id, page.page_index)
                page_views.append(
                    {
                        "index": page.page_index,
                        "data_uri": to_data_uri(page),
                        "rejected": True,
                        "reasons": ocr_verdict.reasons,
                    }
                )
                continue

            store.save_transcription(image_id, ocr_page, page_text, source)

            if isinstance(struct_res, Exception):
                structured = {"error": str(struct_res)}
            else:
                structured = struct_res
            store.save_structured(image_id, ocr_page, structured)

            page_views.append(                                    # thumbnail + transcription
                {
                    "index": page.page_index,
                    "data_uri": to_data_uri(page),
                    "text": page_text,
                }
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
