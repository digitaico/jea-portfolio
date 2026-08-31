"""``OcrEngine`` adapter backed by Gemini Flash (google-genai, async).

This is the only file that knows about google-genai. Because the pipeline
depends on the ``OcrEngine`` port, replacing this with a local VLM later is a
drop-in swap (LSP) done in the composition root.
"""

import asyncio

import cv2

from google import genai
from google.genai import errors, types

from app.domain.errors import PageError
from app.domain.ports import OcrEngine, PageImage

# Spanish-first, free-form transcription. No schema, no summarizing.
_TRANSCRIPTION_PROMPT = (
    "Transcribe verbatim all text visible in this image. "
    "The text is most likely in Spanish. "
    "Preserve the natural reading order and line breaks. "
    "Do not summarize, translate, explain, or invent content. "
    "If a word is illegible, write [ilegible]. "
    "Return plain text only, with no extra commentary."
)

# HTTP status codes worth retrying (rate limit + transient server errors).
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class GeminiFlashOcr(OcrEngine):
    """Transcribe one image per call, with bounded exponential backoff."""

    def __init__(
        self,
        api_key: str,
        model_name: str,
        max_retries: int = 3,
        base_delay: float = 1.0,
    ) -> None:
        # The client is created once and reused across requests (it holds the
        # HTTP session). The composition root builds this adapter a single time.
        self._client = genai.Client(api_key=api_key)
        self._model = model_name
        self._max_retries = max_retries
        self._base_delay = base_delay

    async def transcribe(self, image: PageImage) -> str:
        image_part = types.Part.from_bytes(
            data=self._encode_png(image), mime_type="image/png"
        )
        for attempt in range(self._max_retries):
            try:
                response = await self._client.aio.models.generate_content(
                    model=self._model,
                    contents=[_TRANSCRIPTION_PROMPT, image_part],
                )
                return (response.text or "").strip()
            except errors.APIError as exc:
                retryable = exc.code in _RETRYABLE_STATUS
                last_attempt = attempt == self._max_retries - 1
                if retryable and not last_attempt:
                    await asyncio.sleep(self._base_delay * (2 ** attempt))
                    continue
                raise PageError(f"Gemini transcription failed: {exc}") from exc
        raise PageError("Gemini transcription exhausted retries.")

    @staticmethod
    def _encode_png(image: PageImage) -> bytes:
        # PNG is lossless; after the resize stage the payload is already bounded.
        success, buffer = cv2.imencode(".png", image)
        if not success:
            raise PageError("Failed to encode image for transcription.")
        return buffer.tobytes()
