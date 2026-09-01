"""Ports (abstractions) the ingest layer depends on."""

from abc import ABC, abstractmethod

from app.domain.models import LoadedImage, QualityReport


class QualityAssessor(ABC):
    """Measure objective quality metrics on a decoded page.

    SRP: it only measures — it never mutates pixels. The result is returned (and
    persisted) so preprocessing or any other service can consume it later,
    instead of each step measuring the same things again (DIP for that future).
    """

    @abstractmethod
    def assess(self, page: LoadedImage) -> QualityReport:
        ...


class PageDecoder(ABC):
    """Decode one upload into one or more RGB pages.

    ISP: a decoder only decodes. LSP: every decoder returns the same
    LoadedImage contract, so PDF and image decoders are interchangeable to
    the caller. A multi-page source (PDF) returns a list with page_count > 1.
    """

    @abstractmethod
    def supports(self, filename: str, content_type: str | None) -> bool:
        """Return True if this decoder can handle the file."""

    @abstractmethod
    def decode(
        self, data: bytes, filename: str, content_type: str | None
    ) -> list[LoadedImage]:
        """Decode bytes into RGB pages (raises DecodeError on failure)."""


class Preprocessor(ABC):
    """Clean a page by consuming its quality metrics (no re-measuring)."""

    @abstractmethod
    def process(self, page: LoadedImage) -> LoadedImage:
        """Return a preprocessed copy; reads page.quality, records page.notes."""


class ImageStore(ABC):
    """Persist decoded pages, processed pages, and metrics. Swappable (OCP/LSP)."""

    @abstractmethod
    def save(self, image_id: str, page: LoadedImage) -> str:
        """Write <id>_p<N>_original.png (+ _quality.json); return the image path."""

    @abstractmethod
    def save_processed(self, image_id: str, page: LoadedImage) -> str:
        """Write <id>_p<N>_processed.png (+ _report.json); return the image path."""
