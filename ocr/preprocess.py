"""VLM-tuned image cleanup.

The output stays continuous-tone (grayscale/colour) on purpose: there is NO
thresholding/binarization of the delivered image, because vision models read
continuous-tone images better than 1-bit ones — this matters most for
handwriting, where thresholding destroys stroke detail.

SRP within a class: every stage is a small private method, so the chain in
``clean`` is trivial to reorder or disable while tuning.
"""

import cv2
import numpy as np

from app.domain.ports import PageImage, Preprocessor


class OpenCvPreprocessor(Preprocessor):
    """Deskew -> dewarp -> illumination -> denoise -> resize."""

    def __init__(self, max_dim: int) -> None:
        self._max_dim = max_dim

    def clean(self, image: PageImage) -> PageImage:
        image = self._deskew(image)
        image = self._dewarp(image)
        image = self._normalize_illumination(image)
        image = self._denoise(image)
        image = self._resize(image)
        return image

    # -- deskew ------------------------------------------------------------- #
    def _deskew(self, image: PageImage) -> PageImage:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Threshold is used ONLY to locate text pixels for measuring the skew
        # angle. The angle is applied to the original colour image; the
        # thresholded version is never returned.
        inverted = cv2.bitwise_not(gray)
        _, mask = cv2.threshold(
            inverted, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        coords = np.column_stack(np.where(mask > 0)).astype(np.float32)
        if coords.shape[0] < 100:  # too little signal to trust an angle
            return image

        angle = cv2.minAreaRect(coords)[-1]
        if angle > 45:  # normalize into a small correction range
            angle -= 90
        # Only correct plausible small skews; anything larger is likely a
        # mis-detection and is left alone for the MVP.
        if abs(angle) < 0.5 or abs(angle) > 15:
            return image
        return self._rotate(image, angle)

    @staticmethod
    def _rotate(image: PageImage, angle: float) -> PageImage:
        height, width = image.shape[:2]
        center = (width / 2.0, height / 2.0)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(
            image,
            matrix,
            (width, height),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )

    # -- dewarp ------------------------------------------------------------- #
    def _dewarp(self, image: PageImage) -> PageImage:
        # Conservative perspective correction: only fires when a large,
        # four-sided document boundary is found. Otherwise it is a passthrough.
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        contours, _ = cv2.findContours(
            edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        if not contours:
            return image

        image_area = image.shape[0] * image.shape[1]
        largest = max(contours, key=cv2.contourArea)
        perimeter = cv2.arcLength(largest, True)
        quad = cv2.approxPolyDP(largest, 0.02 * perimeter, True)

        # Require a 4-corner shape covering a big fraction of the frame before
        # trusting it as the page boundary.
        if len(quad) != 4 or cv2.contourArea(quad) < 0.30 * image_area:
            return image
        return self._four_point_warp(image, quad.reshape(4, 2).astype("float32"))

    @staticmethod
    def _four_point_warp(image: PageImage, pts: np.ndarray) -> PageImage:
        # Order the corners as top-left, top-right, bottom-right, bottom-left.
        rect = np.zeros((4, 2), dtype="float32")
        coord_sum = pts.sum(axis=1)
        rect[0] = pts[np.argmin(coord_sum)]  # top-left  (smallest x+y)
        rect[2] = pts[np.argmax(coord_sum)]  # bottom-right (largest x+y)
        coord_diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(coord_diff)]  # top-right (smallest y-x)
        rect[3] = pts[np.argmax(coord_diff)]  # bottom-left (largest y-x)

        (tl, tr, br, bl) = rect
        width = int(max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl)))
        height = int(max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl)))
        if width < 10 or height < 10:  # degenerate quad, skip
            return image

        destination = np.array(
            [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
            dtype="float32",
        )
        matrix = cv2.getPerspectiveTransform(rect, destination)
        return cv2.warpPerspective(image, matrix, (width, height))

    # -- illumination ------------------------------------------------------- #
    @staticmethod
    def _normalize_illumination(image: PageImage) -> PageImage:
        # CLAHE on the L channel evens out uneven lighting and shadows from
        # phone photos without shifting colour balance.
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_channel = clahe.apply(l_channel)
        merged = cv2.merge((l_channel, a_channel, b_channel))
        return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

    # -- denoise ------------------------------------------------------------ #
    @staticmethod
    def _denoise(image: PageImage) -> PageImage:
        # Edge-preserving and light: removes grain while keeping stroke edges
        # crisp for the vision model.
        return cv2.bilateralFilter(image, d=5, sigmaColor=50, sigmaSpace=50)

    # -- resize ------------------------------------------------------------- #
    def _resize(self, image: PageImage) -> PageImage:
        height, width = image.shape[:2]
        longest = max(height, width)
        if longest <= self._max_dim:
            return image  # never upscale
        scale = self._max_dim / longest
        new_size = (int(width * scale), int(height * scale))
        return cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)
