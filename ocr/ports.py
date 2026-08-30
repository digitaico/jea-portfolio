"""Ports: the abstract contracts the pipeline depends on.

These four ABCs are the seams of the whole design:

* ISP  — each port is small and single-purpose, so no adapter is forced to
         implement methods it does not need.
* DIP  — the pipeline (high-level policy) depends on THESE abstractions, not on
         PyMuPDF / OpenCV / google-genai (low-level detail).
* LSP  — any concrete implementation must be substitutable wherever its port is
         expected, honouring the same contract.
"""

from abc import ABC, abstractmethod

import numpy as np

from app.domain.models import DocumentResult

# A page image is an OpenCV/NumPy array of shape (H, W, 3) in BGR order.
PageImage = np.ndarray


class SourceLoader(ABC):
    """Turn raw uploaded bytes into one image per page."""

    @abstractmethod
    def supports(self, filename: str, content_type: str | None) -> bool:
        """Return True if this loader can decode the given file."""

    @abstractmethod
    def load(self, data: bytes, filename: str) -> list[PageImage]:
        """Decode bytes into a list of page images (single image => 1 element)."""


class Preprocessor(ABC):
    """Clean a single page image so it is ready for a vision model."""

    @abstractmethod
    def clean(self, image: PageImage) -> PageImage:
        """Return a cleaned copy of the image (no binarization)."""


class OcrEngine(ABC):
    """Transcribe a single cleaned image into text."""

    @abstractmethod
    async def transcribe(self, image: PageImage) -> str:
        """Return the transcribed text for one page image."""


class ResultSink(ABC):
    """Persist a finished ``DocumentResult``."""

    @abstractmethod
    def save(self, result: DocumentResult) -> None:
        """Write the result somewhere durable."""
