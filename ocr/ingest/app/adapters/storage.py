"""Filesystem store. One folder per upload, named by its UUID.

    storage/<image_id>/
        p<N>_original.png     decoded, normalized RGB (QC baseline)
        p<N>_processed.png    preprocessed RGB
        p<N>_quality.json     metrics + provenance
        p<N>_report.json      preprocessing decisions
        p<N>.json             OCR result (text + provenance)
        p<N>.txt              OCR plain text

One job (SRP); behind the ImageStore port so an S3 store is a drop-in (DIP/OCP).
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

from app.domain.models import LoadedImage
from app.domain.ports import ImageStore


class FilesystemImageStore(ImageStore):
    def __init__(self, storage_dir: Path) -> None:
        self._dir = storage_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def _page_dir(self, image_id: str) -> Path:
        d = self._dir / image_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def save(self, image_id: str, page: LoadedImage) -> str:
        d = self._page_dir(image_id)
        base = f"p{page.page_index}"
        image_path = d / f"{base}_original.png"
        Image.fromarray(page.rgb, mode="RGB").save(image_path, format="PNG")

        if page.quality is not None:
            record = {
                "image_id": image_id,
                "page_index": page.page_index,
                "page_count": page.page_count,
                "upload_date": datetime.now(timezone.utc).isoformat(),
                **page.quality.to_dict(),
            }
            (d / f"{base}_quality.json").write_text(
                json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        return str(image_path)

    def save_processed(self, image_id: str, page: LoadedImage) -> str:
        d = self._page_dir(image_id)
        base = f"p{page.page_index}"
        image_path = d / f"{base}_processed.png"
        Image.fromarray(page.rgb, mode="RGB").save(image_path, format="PNG")

        if page.notes:
            (d / f"{base}_report.json").write_text(
                json.dumps({"notes": page.notes}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        return str(image_path)

    def save_transcription(
        self, image_id: str, page: LoadedImage, text: str, source: str
    ) -> str:
        d = self._page_dir(image_id)
        base = f"p{page.page_index}"
        record = {
            "image_id": image_id,
            "page_index": page.page_index,
            "page_count": page.page_count,
            "source": source,                 # "processed" | "original"
            "transcribed_at": datetime.now(timezone.utc).isoformat(),
            "text": text,
        }
        (d / f"{base}.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (d / f"{base}.txt").write_text(text, encoding="utf-8")
        return str(d / f"{base}.json")

    def save_structured(self, image_id: str, page: LoadedImage, data: dict) -> str:
        d = self._page_dir(image_id)
        path = d / f"p{page.page_index}_structured.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(path)

    def remove_page(self, image_id: str, page_index: int) -> None:
        d = self._dir / image_id
        if not d.exists():
            return
        # Exact page prefix so p1 doesn't also match p10, p11, ...
        for pattern in (f"p{page_index}_*", f"p{page_index}.*"):
            for f in d.glob(pattern):
                try:
                    f.unlink()
                except OSError:
                    pass
        try:  # drop the folder if this was the only page
            if not any(d.iterdir()):
                d.rmdir()
        except OSError:
            pass
