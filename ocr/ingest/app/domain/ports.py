"""Ports (abstractions) the ingest layer depends on."""

from abc import ABC, abstractmethod

from app.domain.models import LoadedImage


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
