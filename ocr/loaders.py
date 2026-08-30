"""Concrete ``SourceLoader`` adapters.

Each loader has one job (SRP) and declares which files it supports, so the
pipeline can pick the right one. Adding TIFF-only handling later means writing a
new loader here and registering it — nothing else changes (OCP).
"""

import io
from pathlib import PurePath

import cv2
import fitz  # PyMuPDF
import numpy as np
from PIL import Image

from app.domain.ports import PageImage, SourceLoader

_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


class PdfLoader(SourceLoader):
    """Rasterize every PDF page to a BGR image using PyMuPDF."""

    def __init__(self, dpi: int) -> None:
        # The DPI is injected from settings; the loader never reads the env.
        self._dpi = dpi

    def supports(self, filename: str, content_type: str | None) -> bool:
        if content_type == "application/pdf":
            return True
        return PurePath(filename).suffix.lower() == ".pdf"

    def load(self, data: bytes, filename: str) -> list[PageImage]:
        images: list[PageImage] = []
        with fitz.open(stream=data, filetype="pdf") as doc:
            for page in doc:
                pixmap = page.get_pixmap(dpi=self._dpi)
                array = np.frombuffer(pixmap.samples, dtype=np.uint8)
                array = array.reshape(pixmap.height, pixmap.width, pixmap.n)
                images.append(self._to_bgr(array, pixmap.n))
        return images

    @staticmethod
    def _to_bgr(array: np.ndarray, channels: int) -> PageImage:
        # Normalize whatever PyMuPDF produced into 3-channel BGR for OpenCV.
        if channels == 4:  # RGBA
            return cv2.cvtColor(array, cv2.COLOR_RGBA2BGR)
        if channels == 3:  # RGB
            return cv2.cvtColor(array, cv2.COLOR_RGB2BGR)
        return cv2.cvtColor(array, cv2.COLOR_GRAY2BGR)  # single channel


class ImageLoader(SourceLoader):
    """Decode a single image file into a one-page list."""

    def supports(self, filename: str, content_type: str | None) -> bool:
        if content_type and content_type.startswith("image/"):
            return True
        return PurePath(filename).suffix.lower() in _IMAGE_EXTENSIONS

    def load(self, data: bytes, filename: str) -> list[PageImage]:
        pil_image = Image.open(io.BytesIO(data)).convert("RGB")
        rgb = np.array(pil_image)
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        return [bgr]  # single image == one-page document
