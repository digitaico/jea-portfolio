"""Domain models."""

from dataclasses import dataclass

import numpy as np


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
