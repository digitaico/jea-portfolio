"""Metric-driven preprocessing (Stage 4).

Each step *consumes* the quality metrics measured in Stage 3 and decides for
itself whether to act and how strong to be. It never measures the image again.
Output stays continuous-tone RGB (never binarized) and gentle by default, since
some orders are handwritten. There is no orientation step anywhere.

Design (OCP): each step is a small class implementing PreprocessStep. The
MetricDrivenPreprocessor runs an ordered list of them and satisfies the
Preprocessor port. Reorder / add / remove by editing the list in the composition
root — no existing step changes.
"""

from abc import ABC, abstractmethod
from dataclasses import replace

import cv2
import numpy as np

from app.domain.models import LoadedImage, QualityReport
from app.domain.ports import Preprocessor

# Thresholds (algorithm params, not env values).
_CROP_MAX_FILL = 0.90     # crop only if paper fills less than this of the frame
_SKEW_MIN = 0.5           # degrees; below this, not worth rotating
_SKEW_MAX = 15.0          # degrees; above this, treat as unreliable and skip
_ILLUM_THRESHOLD = 0.06   # illumination_unevenness above this => normalize
_NOISE_THRESHOLD = 2.0    # noise_sigma above this => denoise


class PreprocessStep(ABC):
    """One metric-gated transformation. Returns (image, note-or-None)."""

    @abstractmethod
    def apply(self, rgb: np.ndarray, q: QualityReport) -> tuple[np.ndarray, str | None]:
        ...


class CropToDocument(PreprocessStep):
    """Crop to the detected page when the frame has background to remove."""

    def apply(self, rgb, q):
        if q.document_bbox is None or q.page_fill_ratio >= _CROP_MAX_FILL:
            return rgb, None
        h, w = rgb.shape[:2]
        bx = int(q.document_bbox["x"] * w)
        by = int(q.document_bbox["y"] * h)
        bw = int(q.document_bbox["w"] * w)
        bh = int(q.document_bbox["h"] * h)
        # clamp to bounds and require a sane region
        bx, by = max(bx, 0), max(by, 0)
        bw, bh = min(bw, w - bx), min(bh, h - by)
        if bw < 10 or bh < 10:
            return rgb, None
        return rgb[by:by + bh, bx:bx + bw], f"Recorte a documento ({bw}x{bh})"


class Deskew(PreprocessStep):
    """Rotate by the measured skew angle (advisory; small angles only)."""

    def apply(self, rgb, q):
        angle = q.skew_angle
        if abs(angle) < _SKEW_MIN or abs(angle) > _SKEW_MAX:
            return rgb, None
        h, w = rgb.shape[:2]
        matrix = cv2.getRotationMatrix2D((w / 2.0, h / 2.0), angle, 1.0)
        out = cv2.warpAffine(
            rgb, matrix, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
        )
        return out, f"Enderezado {angle:+.1f} grados"


class Illumination(PreprocessStep):
    """CLAHE, strength scaled to the measured unevenness (capped, gentle)."""

    def apply(self, rgb, q):
        if q.illumination_unevenness <= _ILLUM_THRESHOLD:
            return rgb, None
        clip = float(np.clip(1.0 + q.illumination_unevenness * 10.0, 1.0, 2.5))
        lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        l = cv2.createCLAHE(clipLimit=clip, tileGridSize=(8, 8)).apply(l)
        out = cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2RGB)
        strength = "leve" if clip < 1.6 else "media" if clip < 2.1 else "fuerte"
        return out, f"Iluminacion CLAHE {strength}"


class Denoise(PreprocessStep):
    """Edge-preserving denoise, strength scaled to measured noise (light)."""

    def apply(self, rgb, q):
        if q.noise_sigma <= _NOISE_THRESHOLD:
            return rgb, None
        sigma_color = float(np.clip(q.noise_sigma * 6.0, 25.0, 90.0))
        out = cv2.bilateralFilter(rgb, d=5, sigmaColor=sigma_color, sigmaSpace=7)
        level = "leve" if q.noise_sigma < 4.0 else "moderada"
        return out, f"Ruido reduccion {level}"


class Resize(PreprocessStep):
    """Downscale to a max dimension (never upscale)."""

    def __init__(self, max_dim: int) -> None:
        self._max_dim = max_dim

    def apply(self, rgb, q):
        h, w = rgb.shape[:2]
        longest = max(h, w)
        if longest <= self._max_dim:
            return rgb, None
        scale = self._max_dim / longest
        nw, nh = int(w * scale), int(h * scale)
        out = cv2.resize(rgb, (nw, nh), interpolation=cv2.INTER_AREA)
        return out, f"Escalado a {nw}x{nh}"


class MetricDrivenPreprocessor(Preprocessor):
    """Run an ordered list of metric-gated steps; record decisions (SRP + OCP)."""

    def __init__(self, steps: list[PreprocessStep]) -> None:
        self._steps = steps

    def process(self, page: LoadedImage) -> LoadedImage:
        if page.quality is None:
            # Without metrics there is nothing to consume; return unchanged.
            return replace(page, notes=["Sin metricas: sin cambios"])

        rgb = page.rgb
        q = page.quality
        notes: list[str] = []
        for step in self._steps:
            rgb, note = step.apply(rgb, q)
            if note:
                notes.append(note)
        if not notes:
            notes.append("Sin cambios (imagen ya adecuada)")
        h, w = rgb.shape[:2]
        return replace(page, rgb=rgb, width=w, height=h, notes=notes)
