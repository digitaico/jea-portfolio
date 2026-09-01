"""Ports (abstractions) the ingest layer depends on."""

from abc import ABC, abstractmethod

from app.domain.models import LoadedImage, QualityReport, ReadabilityVerdict


class QualityAssessor(ABC):
    """Measure objective quality metrics on a decoded page.

    SRP: it only measures — it never mutates pixels. The result is returned (and
    persisted) so preprocessing or any other service can consume it later,
    instead of each step measuring the same things again (DIP for that future).
    """

    @abstractmethod
    def assess(self, page: LoadedImage) -> QualityReport:
        ...


class ReadabilityGate(ABC):
    """Decide, from the quality metrics, whether a page is worth OCR'ing.

    SRP: assessment measures; the gate judges. It consumes a QualityReport and
    returns a verdict; it does not touch pixels or storage.
    """

    @abstractmethod
    def evaluate(self, quality: QualityReport) -> ReadabilityVerdict:
        ...


class TranscriptionGate(ABC):
    """Judge readability from the OCR output itself (the model is the real test).

    Empty or mostly-illegible transcription => not readable.
    """

    @abstractmethod
    def evaluate(self, text: str) -> ReadabilityVerdict:
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


class OcrProvider(ABC):
    """Transcribe one page image to text. Gemini today, others tomorrow (LSP)."""

    @abstractmethod
    async def transcribe(self, page: LoadedImage) -> str:
        """Return the free-form transcription of the page (raises on failure)."""


class StructuredExtractor(ABC):
    """Extract structured fields (by semantic area) from one page image."""

    @abstractmethod
    async def extract(self, page: LoadedImage) -> dict:
        """Return a dict keyed by semantic area; missing values are null."""


class ImageStore(ABC):
    """Persist decoded pages, processed pages, metrics, and transcriptions."""

    @abstractmethod
    def save(self, image_id: str, page: LoadedImage) -> str:
        """Write <id>_p<N>_original.png (+ _quality.json); return the image path."""

    @abstractmethod
    def save_processed(self, image_id: str, page: LoadedImage) -> str:
        """Write <id>_p<N>_processed.png (+ _report.json); return the image path."""

    @abstractmethod
    def save_transcription(self, image_id: str, page: LoadedImage, text: str, source: str) -> str:
        """Write <id>_p<N>.json + <id>_p<N>.txt; return the json path."""

    @abstractmethod
    def save_structured(self, image_id: str, page: LoadedImage, data: dict) -> str:
        """Write <id>_p<N>_structured.json; return its path."""

    @abstractmethod
    def remove_page(self, image_id: str, page_index: int) -> None:
        """Delete all stored files for one page (used when OCR finds it unreadable)."""
