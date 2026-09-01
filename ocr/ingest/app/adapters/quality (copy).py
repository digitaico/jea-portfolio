"""Image quality assessment (Stage 6).

Measures objective, per-page metrics on the decoded original and returns a
QualityReport. Pure measurement — it does not change a single pixel (SRP). The
metrics are persisted so preprocessing (later) and any other service can read
them instead of recomputing.
"""

import cv2
import numpy as np

from app.domain.models import LoadedImage, QualityReport
from app.domain.ports import QualityAssessor

# Immerkaer noise kernel.
_NOISE_KERNEL = np.array([[1, -2, 1], [-2, 4, -2], [1, -2, 1]], dtype=np.float32)

# Sharpness is measured on the document region resized so its longest side is
# this many pixels — makes the Laplacian variance comparable across resolutions.
_SHARPNESS_NORM_DIM = 1000


class OpenCvQualityAssessor(QualityAssessor):
    def assess(self, page: LoadedImage) -> QualityReport:
        rgb = page.rgb
        h, w = rgb.shape[:2]
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        fill, bbox = self._document_region(gray)

        return QualityReport(
            width=w,
            height=h,
            megapixels=round(w * h / 1_000_000, 3),
            sharpness=round(self._sharpness(gray, bbox), 2),
            noise_sigma=round(self._noise_sigma(gray), 3),
            brightness=round(float(gray.mean()), 2),
            contrast=round(float(gray.std()), 2),
            illumination_unevenness=round(self._illumination_unevenness(rgb), 4),
            skew_angle=round(self._skew_angle(gray), 2),
            page_fill_ratio=fill,
            document_bbox=bbox,
        )

    # -- individual metrics -------------------------------------------------- #
    @staticmethod
    def _sharpness(gray: np.ndarray, bbox: "dict | None") -> float:
        # Laplacian variance, but made comparable across captures:
        #  1) crop to the document region (blur that matters is blur on the
        #     paper, not on the floor/background),
        #  2) normalize resolution (variance scales with size), so the same
        #     scene at 12MP and 1MP yields a comparable number.
        region = gray
        if bbox is not None:
            h, w = gray.shape
            x = max(int(bbox["x"] * w), 0)
            y = max(int(bbox["y"] * h), 0)
            bw = min(int(bbox["w"] * w), w - x)
            bh = min(int(bbox["h"] * h), h - y)
            if bw >= 10 and bh >= 10:
                region = gray[y:y + bh, x:x + bw]

        longest = max(region.shape[:2])
        if longest > _SHARPNESS_NORM_DIM:
            scale = _SHARPNESS_NORM_DIM / longest
            region = cv2.resize(
                region,
                (int(region.shape[1] * scale), int(region.shape[0] * scale)),
                interpolation=cv2.INTER_AREA,
            )
        return float(cv2.Laplacian(region, cv2.CV_64F).var())

    @staticmethod
    def _noise_sigma(gray: np.ndarray) -> float:
        h, w = gray.shape
        if w < 3 or h < 3:
            return 0.0
        conv = np.abs(cv2.filter2D(gray.astype(np.float32), -1, _NOISE_KERNEL))
        return float(conv.sum() * np.sqrt(np.pi / 2.0) / (6.0 * (w - 2) * (h - 2)))

    @staticmethod
    def _illumination_unevenness(rgb: np.ndarray) -> float:
        l = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)[:, :, 0].astype(np.float32)
        h, w = l.shape
        sigma = max(min(h, w) / 8.0, 11.0)
        background = cv2.GaussianBlur(l, (0, 0), sigma)  # illumination field
        return float(background.std() / (background.mean() + 1e-6))

    @staticmethod
    def _skew_angle(gray: np.ndarray) -> float:
        inverted = cv2.bitwise_not(gray)
        _, mask = cv2.threshold(inverted, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        coords = np.column_stack(np.where(mask > 0)).astype(np.float32)
        if coords.shape[0] < 100:
            return 0.0
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = 90 + angle
        elif angle > 45:
            angle = angle - 90
        return float(angle)

    @staticmethod
    def _document_region(gray: np.ndarray) -> tuple[float, "dict | None"]:
        # Paper is brighter than the background (floor/desk). Threshold, close
        # the text holes, and take the large bright regions as the document.
        # page_fill_ratio = paper area / frame; low => lots of background to crop.
        # document_bbox = normalized crop enclosing all paper (union of regions).
        h, w = gray.shape
        frame = float(h * w)
        _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
        closed = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        regions = [c for c in contours if cv2.contourArea(c) > 0.03 * frame]
        if not regions:
            return 0.0, None

        fill = sum(cv2.contourArea(c) for c in regions) / frame
        x0, y0, x1, y1 = w, h, 0, 0
        for c in regions:  # union bounding box of all paper regions
            x, y, bw_, bh_ = cv2.boundingRect(c)
            x0, y0 = min(x0, x), min(y0, y)
            x1, y1 = max(x1, x + bw_), max(y1, y + bh_)
        bbox = {
            "x": round(x0 / w, 4),
            "y": round(y0 / h, 4),
            "w": round((x1 - x0) / w, 4),
            "h": round((y1 - y0) / h, 4),
        }
        return round(float(fill), 4), bbox
