"""Concrete decoders. Each has one job (SRP); a new format = a new decoder (OCP).

Both output the same LoadedImage contract in RGB, uint8. No thresholding or
preprocessing here — Stage 2 only decodes and normalizes colour space.
"""

import io
from pathlib import PurePath

import numpy as np
import pillow_heif
from PIL import Image, ImageOps

from app.domain.errors import DecodeError
from app.domain.models import LoadedImage
from app.domain.ports import PageDecoder

# Register HEIC/HEIF support into Pillow (iPhone camera default).
pillow_heif.register_heif_opener()

_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".heic", ".heif"}


class ImageDecoder(PageDecoder):
    """Decode a single-image upload (local file or camera capture) to RGB."""

    def supports(self, filename: str, content_type: str | None) -> bool:
        if content_type and content_type.startswith("image/"):
            return True
        return PurePath(filename).suffix.lower() in _IMAGE_EXTENSIONS

    def decode(
        self, data: bytes, filename: str, content_type: str | None
    ) -> list[LoadedImage]:
        try:
            with Image.open(io.BytesIO(data)) as img:
                fmt = img.format or "IMAGE"
                img = ImageOps.exif_transpose(img)  # honour phone rotation
                rgb = np.asarray(img.convert("RGB"))
        except Exception as exc:  # noqa: BLE001 - any failure => not usable
            raise DecodeError(f"Could not decode image '{filename}': {exc}") from exc

        height, width = rgb.shape[:2]
        return [
            LoadedImage(
                rgb=rgb,
                width=width,
                height=height,
                source_format=fmt,
                source_filename=filename,
                size_bytes=len(data),
                page_index=0,
                page_count=1,
            )
        ]


class PdfDecoder(PageDecoder):
    """Rasterize every page of a PDF to an RGB image via PyMuPDF."""

    def __init__(self, dpi: int) -> None:
        # DPI injected from settings; the decoder never reads the environment.
        self._dpi = dpi

    def supports(self, filename: str, content_type: str | None) -> bool:
        if content_type == "application/pdf":
            return True
        return PurePath(filename).suffix.lower() == ".pdf"

    def decode(
        self, data: bytes, filename: str, content_type: str | None
    ) -> list[LoadedImage]:
        import fitz  # PyMuPDF; imported lazily to keep import cost off the UI path

        try:
            doc = fitz.open(stream=data, filetype="pdf")
        except Exception as exc:  # noqa: BLE001
            raise DecodeError(f"Could not open PDF '{filename}': {exc}") from exc

        pages: list[LoadedImage] = []
        with doc:
            count = doc.page_count
            if count == 0:
                raise DecodeError(f"PDF '{filename}' has no pages.")
            for index, page in enumerate(doc):
                pixmap = page.get_pixmap(dpi=self._dpi)
                arr = np.frombuffer(pixmap.samples, dtype=np.uint8)
                arr = arr.reshape(pixmap.height, pixmap.width, pixmap.n)
                rgb = self._to_rgb(arr, pixmap.n)
                pages.append(
                    LoadedImage(
                        rgb=rgb,
                        width=pixmap.width,
                        height=pixmap.height,
                        source_format="PDF",
                        source_filename=filename,
                        size_bytes=len(data),
                        page_index=index,
                        page_count=count,
                    )
                )
        return pages

    @staticmethod
    def _to_rgb(arr: np.ndarray, channels: int) -> np.ndarray:
        if channels == 4:      # RGBA -> drop alpha
            return arr[:, :, :3].copy()
        if channels == 1:      # grayscale -> RGB
            return np.repeat(arr, 3, axis=2)
        return arr             # already RGB
