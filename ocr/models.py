"""Pydantic v2 models returned by the API and persisted to disk."""

from pydantic import BaseModel, computed_field


class Page(BaseModel):
    """A single transcribed page. Free-form: ``text`` is the whole page."""

    index: int
    text: str


class DocumentResult(BaseModel):
    """The full transcription result for one uploaded document."""

    source_filename: str
    model: str
    pages: list[Page]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def full_text(self) -> str:
        """All page texts joined in reading order (used for the .txt output)."""
        return "\n\n".join(page.text for page in self.pages)
