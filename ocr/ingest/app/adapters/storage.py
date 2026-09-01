"""Filesystem store for decoded pages + their quality metrics.

Persists the decoded/normalized original as lossless PNG and the quality report
as JSON. Naming keeps the `_original` suffix so a separate preprocessing service
can later add `<id>_p<N>_processed.png` beside it. One job (SRP); behind the
ImageStore port so an S3 store is a drop-in later (DIP/OCP).
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

    def save(self, image_id: str, page: LoadedImage) -> str:
        base = f"{image_id}_p{page.page_index}"
        image_path = self._dir / f"{base}_original.png"
        Image.fromarray(page.rgb, mode="RGB").save(image_path, format="PNG")

        if page.quality is not None:
            # Provenance (image_id, upload_date) is added here, not in the
            # assessor: the assessor only measures pixels; the store knows the
            # id and the write moment.
            record = {
                "image_id": image_id,
                "page_index": page.page_index,
                "page_count": page.page_count,
                "upload_date": datetime.now(timezone.utc).isoformat(),
                **page.quality.to_dict(),
            }
            (self._dir / f"{base}_quality.json").write_text(
                json.dumps(record, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        return str(image_path)

    def save_processed(self, image_id: str, page: LoadedImage) -> str:
        base = f"{image_id}_p{page.page_index}"
        image_path = self._dir / f"{base}_processed.png"
        Image.fromarray(page.rgb, mode="RGB").save(image_path, format="PNG")

        if page.notes:
            (self._dir / f"{base}_report.json").write_text(
                json.dumps({"notes": page.notes}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        return str(image_path)
