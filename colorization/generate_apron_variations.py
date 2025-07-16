"""generate_apron_variations.py

Generate multiple colour-ways of the apron template using automatic mask detection
(derived colour-range thresholding) and a CSV of target body & pockets colours.

The pipeline:
1. Load the template image found in assets/template.jpg
2. Detect body & pocket regions automatically (no manual masks) by running
   K-means on the pixel colours (LAB space). The largest cluster is assumed
   background, the 2nd largest -> body, the 3rd largest -> pockets.
3. Iterate over data/color_combinations.csv and recolour the template for
   every row. Hue/saturation is swapped, lightness of the pockets is softly
   blended toward the target so that creases remain visible.
4. For every combination four control snapshots are produced:
       a) original template
       b) body mask overlay (red)
       c) pockets mask overlay (green)
       d) recoloured output
5. The recoloured result and the control collage are saved to
   output/cursor-YYYY-MM-DD/.

The script is self-contained – just run `python generate_apron_variations.py`.
"""

from __future__ import annotations

import csv
import datetime as _dt
import os
from pathlib import Path
from typing import Tuple

import cv2  # type: ignore
import numpy as np

# ---------------------------------------------------------
# Hard-coded resources (change here if you move files)
# ---------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_IMG = SCRIPT_DIR / "assets" / "template.jpg"
CSV_COLORS = SCRIPT_DIR / "data" / "color_combinations.csv"

# Output → colourised images & debug collages
OUT_DIR = SCRIPT_DIR / "output" / f"cursor-{_dt.date.today()}"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

def hex_to_bgr(hex_color: str) -> Tuple[int, int, int]:
    """Convert a #RRGGBB string to (B, G, R) tuple as used by OpenCV."""
    hex_color = hex_color.strip().lstrip("#")
    if len(hex_color) != 6:
        raise ValueError(f"Invalid hex colour: {hex_color}")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (b, g, r)


def detect_masks_color_ranges(
    img_bgr: np.ndarray,
    k: int = 3,
    delta: int = 18,
) -> Tuple[np.ndarray, np.ndarray]:
    """Return `(body_mask, pockets_mask)` by thresholding LAB colour ranges.

    Steps:
    1. Cluster the image colours with K-means (`k` clusters) to obtain
       representative colours (centroids).
    2. Sort clusters by pixel count – background, body, pockets.
    3. For the body & pocket centroids produce a LAB cube of ±`delta` per channel
       and use `cv2.inRange` to derive crisp binary masks.

    This combines the robustness of K-means (automatic centroid discovery) with
    a *colour-range* masking technique, so the final masks **depend only on
    colour ranges**, not the raw K-means labels.
    """
    H, W = img_bgr.shape[:2]

    img_lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    flat = img_lab.reshape((-1, 3)).astype(np.float32)

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _ret, labels, centroids = cv2.kmeans(
        flat, k, None, criteria, 3, cv2.KMEANS_PP_CENTERS
    )
    labels = labels.flatten()

    uniq, counts = np.unique(labels, return_counts=True)
    sorted_ids = uniq[np.argsort(-counts)]  # largest → smallest

    if len(sorted_ids) < 3:
        raise RuntimeError("Could not identify three distinct colour regions")

    _bg_id, body_id, pocket_id = sorted_ids[:3]
    body_centroid = centroids[body_id]
    pockets_centroid = centroids[pocket_id]

    def _range_mask(centroid: np.ndarray) -> np.ndarray:
        lower = np.clip(centroid - delta, 0, 255).astype(np.uint8)
        upper = np.clip(centroid + delta, 0, 255).astype(np.uint8)
        return cv2.inRange(img_lab, lower, upper)

    body_mask = _range_mask(body_centroid)
    pockets_mask = _range_mask(pockets_centroid)

    # Clean masks: remove noise & fill small holes
    kernel = np.ones((3, 3), np.uint8)
    body_mask = cv2.morphologyEx(body_mask, cv2.MORPH_OPEN, kernel)
    body_mask = cv2.morphologyEx(body_mask, cv2.MORPH_CLOSE, kernel)
    pockets_mask = cv2.morphologyEx(pockets_mask, cv2.MORPH_OPEN, kernel)
    pockets_mask = cv2.morphologyEx(pockets_mask, cv2.MORPH_CLOSE, kernel)

    # `inRange` gives 0/255 – convert to 0/1 uint8 for further maths
    body_mask //= 255
    pockets_mask //= 255

    return body_mask.astype(np.uint8), pockets_mask.astype(np.uint8)


def create_overlay(base: np.ndarray, mask: np.ndarray, color: Tuple[int, int, int]) -> np.ndarray:
    """Overlay *mask* on *base* (both BGR) → for visual debugging."""
    overlay_color = np.zeros_like(base)
    overlay_color[mask.astype(bool)] = color
    return cv2.addWeighted(base, 0.7, overlay_color, 0.3, 0)


def recolor(img_bgr: np.ndarray, mask_body: np.ndarray, mask_pockets: np.ndarray,
            body_hex: str, pockets_hex: str) -> np.ndarray:
    """Return a recoloured copy of *img_bgr* using the provided masks & hex colours."""

    body_bgr = np.array([[hex_to_bgr(body_hex)]], dtype=np.uint8)
    pockets_bgr = np.array([[hex_to_bgr(pockets_hex)]], dtype=np.uint8)

    body_lab = cv2.cvtColor(body_bgr, cv2.COLOR_BGR2LAB)[0, 0]
    pockets_lab = cv2.cvtColor(pockets_bgr, cv2.COLOR_BGR2LAB)[0, 0]

    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    L, A, B = cv2.split(lab)

    # Swap hue/saturation (a, b) channels in masked regions
    A[mask_body.astype(bool)] = body_lab[1]
    B[mask_body.astype(bool)] = body_lab[2]

    A[mask_pockets.astype(bool)] = pockets_lab[1]
    B[mask_pockets.astype(bool)] = pockets_lab[2]

    # Gently nudge pocket lightness toward target to preserve folds
    pocket_L_vals = L[mask_pockets.astype(bool)]
    if pocket_L_vals.size:
        target_L = float(pockets_lab[0])
        blend = 0.9  # 90 % toward target
        L[mask_pockets.astype(bool)] = np.clip(
            pocket_L_vals * (1 - blend) + target_L * blend, 0, 255
        ).astype(np.uint8)

    recoloured = cv2.cvtColor(cv2.merge([L, A, B]), cv2.COLOR_LAB2BGR)
    return recoloured


# ---------------------------------------------------------
# Main routine
# ---------------------------------------------------------

def main() -> None:
    print("Loading template …")
    img_bgr = cv2.imread(str(TEMPLATE_IMG))
    if img_bgr is None:
        raise FileNotFoundError(TEMPLATE_IMG)

    print("Detecting mask regions … (this runs only once)")
    mask_body, mask_pockets = detect_masks_color_ranges(img_bgr)

    # Debug overlays
    body_dbg = create_overlay(img_bgr, mask_body, (0, 0, 255))  # red
    pockets_dbg = create_overlay(img_bgr, mask_pockets, (0, 255, 0))  # green

    # Save a standalone debug of masks on original
    cv2.imwrite(str(OUT_DIR / "_debug_body_mask.jpg"), body_dbg)
    cv2.imwrite(str(OUT_DIR / "_debug_pockets_mask.jpg"), pockets_dbg)

    # -----------------------------------------------------
    # Iterate over colour combos
    # -----------------------------------------------------
    with open(CSV_COLORS, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        combos = list(reader)

    print(f"Generating {len(combos)} colour-ways …")

    for row in combos:
        base_name = Path(row["filename"]).stem
        body_hex = row["body_color"].strip()
        pocket_hex = row["pockets_color"].strip()

        print(f" → {base_name}: body {body_hex} | pockets {pocket_hex}")
        out_bgr = recolor(img_bgr, mask_body, mask_pockets, body_hex, pocket_hex)

        # ------------------- save final -------------------
        out_path = OUT_DIR / f"{base_name}.jpg"
        cv2.imwrite(str(out_path), out_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 92])

        # --------------- save control collage -------------
        # stack: [orig, body-overlay, pocket-overlay, recoloured]
        hstack1 = np.hstack([img_bgr, body_dbg])
        hstack2 = np.hstack([pockets_dbg, out_bgr])
        collage = np.vstack([hstack1, hstack2])

        cv2.imwrite(str(OUT_DIR / f"{base_name}_control.jpg"), collage)

    print("Done. Results in", OUT_DIR)


if __name__ == "__main__":
    main() 