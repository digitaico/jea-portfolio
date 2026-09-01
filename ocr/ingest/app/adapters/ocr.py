"""Gemini OCR adapters (Stage 6).

Two capabilities behind two ports:
  - GeminiOcr        -> OcrProvider        : verbatim transcription (text)
  - GeminiExtractor  -> StructuredExtractor : schema-enforced field extraction

Both use the async google-genai client. Prompts are injected from files, and the
extraction schema is built dynamically from the semantic-areas mapping, so what
gets extracted is defined by data (areas.json), not code. This is the only file
that knows about google-genai (DIP/LSP).
"""

import asyncio
import io
import json

import numpy as np
from PIL import Image

from google import genai
from google.genai import errors, types

from app.domain.models import LoadedImage
from app.domain.ports import OcrProvider, StructuredExtractor

_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def _png_part(rgb: np.ndarray) -> types.Part:
    buffer = io.BytesIO()
    Image.fromarray(rgb, mode="RGB").save(buffer, format="PNG")
    return types.Part.from_bytes(data=buffer.getvalue(), mime_type="image/png")


def _areas_as_text(areas: dict) -> str:
    # "- datos_paciente: nombre, identificacion, ..." per area, for the prompt.
    return "\n".join(f"- {area}: {', '.join(fields)}" for area, fields in areas.items())


def _areas_as_schema(areas: dict) -> types.Schema:
    # Object of areas; each area an object of nullable string fields.
    props = {}
    for area, fields in areas.items():
        props[area] = types.Schema(
            type="OBJECT",
            nullable=True,
            properties={f: types.Schema(type="STRING", nullable=True) for f in fields},
        )
    return types.Schema(type="OBJECT", properties=props)


class _GeminiBase:
    def __init__(self, api_key: str, model: str, timeout: float, max_retries: int) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._timeout = timeout
        self._max_retries = max_retries

    async def _generate(self, contents, config):
        for attempt in range(self._max_retries):
            try:
                return await asyncio.wait_for(
                    self._client.aio.models.generate_content(
                        model=self._model, contents=contents, config=config
                    ),
                    timeout=self._timeout,
                )
            except errors.APIError as exc:
                if getattr(exc, "code", None) in _RETRYABLE_STATUS and attempt < self._max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise
            except asyncio.TimeoutError:
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise
        raise RuntimeError("retries exhausted")


class GeminiOcr(_GeminiBase, OcrProvider):
    """Verbatim transcription. Prompt template injected from a file."""

    def __init__(self, api_key, model, temperature, max_output_tokens, timeout,
                 max_retries, prompt_template, language_hint):
        super().__init__(api_key, model, timeout, max_retries)
        self._prompt = prompt_template.format(language_hint=language_hint)
        self._config = types.GenerateContentConfig(
            temperature=temperature, max_output_tokens=max_output_tokens
        )

    async def transcribe(self, page: LoadedImage) -> str:
        response = await self._generate(
            [self._prompt, _png_part(page.rgb)], self._config
        )
        return (response.text or "").strip()


class GeminiExtractor(_GeminiBase, StructuredExtractor):
    """Structured extraction into the areas schema (JSON enforced)."""

    def __init__(self, api_key, model, temperature, max_output_tokens, timeout,
                 max_retries, prompt_template, language_hint, areas):
        super().__init__(api_key, model, timeout, max_retries)
        self._prompt = prompt_template.format(
            language_hint=language_hint, areas=_areas_as_text(areas)
        )
        self._config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            response_mime_type="application/json",
            response_schema=_areas_as_schema(areas),
        )

    async def extract(self, page: LoadedImage) -> dict:
        response = await self._generate(
            [self._prompt, _png_part(page.rgb)], self._config
        )
        return json.loads(response.text or "{}")
