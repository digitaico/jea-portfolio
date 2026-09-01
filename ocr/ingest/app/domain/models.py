"""Domain models."""

from dataclasses import dataclass, field

import numpy as np


@dataclass
class QualityReport:
    """Objective, per-page image-quality metrics measured on the decoded
    original. Pure data: produced by the assessment stage and consumed later by
    preprocessing (or any other service). No thresholds/verdicts here — callers
    decide what a value means for them.
    """

    width: int
    height: int
    megapixels: float
    sharpness: float               # variance of Laplacian (low => blurry)
    noise_sigma: float             # Immerkaer noise estimate
    brightness: float              # mean luminance 0-255
    contrast: float                # luminance std 0-255
    illumination_unevenness: float  # large-scale luminance spread (ratio)
    skew_angle: float              # degrees, normalized to [-45, 45]
    page_fill_ratio: float          # paper area / frame area (low => needs crop)
    document_bbox: "dict | None"    # normalized {x,y,w,h} crop region, or None

    def to_dict(self) -> dict:
        return {
            "width": self.width,
            "height": self.height,
            "megapixels": self.megapixels,
            "sharpness": self.sharpness,
            "noise_sigma": self.noise_sigma,
            "brightness": self.brightness,
            "contrast": self.contrast,
            "illumination_unevenness": self.illumination_unevenness,
            "skew_angle": self.skew_angle,
            "page_fill_ratio": self.page_fill_ratio,
            "document_bbox": self.document_bbox,
        }


@dataclass
class LoadedImage:
    """A single decoded, RGB-normalized page.

    In-memory only: it carries pixels (a NumPy array), so it is a plain
    dataclass, not a Pydantic model. One upload may yield several of these
    (multi-page PDF), hence page_index / page_count for provenance.
    """

    rgb: np.ndarray            # (H, W, 3), uint8, RGB
    width: int
    height: int
    source_format: str         # "JPEG" | "PNG" | "WEBP" | "HEIF" | "PDF" | ...
    source_filename: str
    size_bytes: int            # original upload size
    page_index: int            # 0-based within the source
    page_count: int            # total pages from the source
    quality: "QualityReport | None" = None  # assessment metrics (Stage 3)
    notes: list[str] = field(default_factory=list)  # preprocessing decisions (Stage 4)
