"""Readability gate.

Judges a page's quality metrics against configured thresholds and returns a
verdict with human-readable reasons (Spanish, for the user). Pure decision logic
(SRP): it reads a QualityReport and returns a verdict — no pixels, no storage.

Note: blur (sharpness) is content- and resolution-dependent, so the sharpness
threshold in particular should be tuned against real orders. All thresholds come
from .env.
"""

from app.domain.models import QualityReport, ReadabilityVerdict
from app.domain.ports import ReadabilityGate, TranscriptionGate


class ThresholdReadabilityGate(ReadabilityGate):
    def __init__(
        self,
        min_sharpness: float,
        min_brightness: float,
        max_brightness: float,
        min_contrast: float,
    ) -> None:
        self._min_sharpness = min_sharpness
        self._min_brightness = min_brightness
        self._max_brightness = max_brightness
        self._min_contrast = min_contrast

    def evaluate(self, quality: QualityReport) -> ReadabilityVerdict:
        reasons: list[str] = []
        if quality.sharpness < self._min_sharpness:
            reasons.append("Imagen borrosa: el texto no está enfocado.")
        if quality.brightness < self._min_brightness:
            reasons.append("Imagen demasiado oscura.")
        if quality.brightness > self._max_brightness:
            reasons.append("Imagen demasiado clara o sobreexpuesta.")
        if quality.contrast < self._min_contrast:
            reasons.append("Bajo contraste: el texto casi no se distingue.")
        return ReadabilityVerdict(readable=not reasons, reasons=reasons)


class OcrTranscriptionGate(TranscriptionGate):
    """Readability judged from the transcription the model returned.

    The model is the true test of readability: if it returns nothing, or mostly
    illegible markers, the image is not usable regardless of CV metrics.
    """

    def __init__(self, max_illegible_ratio: float, illegible_token: str = "[ilegible]") -> None:
        self._max_ratio = max_illegible_ratio
        self._token = illegible_token.lower()

    def evaluate(self, text: str) -> ReadabilityVerdict:
        s = (text or "").strip()
        if not s or s.lower().startswith("[error de ocr"):
            return ReadabilityVerdict(False, ["El modelo no pudo leer texto en la imagen."])
        words = s.split()
        if words:
            illegible = s.lower().count(self._token)
            if illegible / len(words) > self._max_ratio:
                return ReadabilityVerdict(False, ["Gran parte del texto resultó ilegible."])
        return ReadabilityVerdict(True, [])
