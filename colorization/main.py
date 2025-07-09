import cv2
import numpy as np
import csv
import os
from datetime import datetime

# ---------------------------------------------------------
# Hard-coded resources (edit here if your paths change)
# ---------------------------------------------------------
SCRIPT_DIR         = os.path.dirname(__file__)
TEMPLATE_IMG       = os.path.join(SCRIPT_DIR, 'assets', 'template.jpg')
MASK_BODY_PATH     = os.path.join(SCRIPT_DIR, 'assets', 'body_mask.png')
MASK_POCKETS_PATH  = os.path.join(SCRIPT_DIR, 'assets', 'pockets_mask.png')
MASK_WEBBING_PATH  = os.path.join(SCRIPT_DIR, 'assets', 'webbing_mask.png')
CSV_COLORS         = os.path.join(SCRIPT_DIR, 'data',   'color_combinations.csv')
OUTPUT_DIR         = os.path.join(SCRIPT_DIR, 'output', datetime.now().strftime('%Y%m%d_%H%M%S'))

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

def hex_to_bgr(hex_color: str) -> tuple[int, int, int]:
    """Converts a #RRGGBB string to BGR tuple used by OpenCV."""
    hex_color = hex_color.strip().lstrip('#')
    if len(hex_color) != 6:
        raise ValueError(f"Invalid hex colour: {hex_color}")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (r, g, b)


def load_mask(path: str, target_shape: tuple[int, int]) -> np.ndarray:
    """Loads a grayscale mask, binarises it, resizes if necessary, returns uint8 0/1 array."""
    mask = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if mask is None:
        raise FileNotFoundError(path)
    if mask.shape[:2] != target_shape:
        mask = cv2.resize(mask, (target_shape[1], target_shape[0]), interpolation=cv2.INTER_NEAREST)
    # binarise → 0 or 1
    _, mask = cv2.threshold(mask, 127, 1, cv2.THRESH_BINARY)
    return mask.astype(np.uint8)


# ---------------------------------------------------------
# Load base image & masks
# ---------------------------------------------------------
img_bgr = cv2.imread(TEMPLATE_IMG)
if img_bgr is None:
    raise FileNotFoundError(TEMPLATE_IMG)
H, W = img_bgr.shape[:2]

mask_body     = load_mask(MASK_BODY_PATH,    (H, W))
mask_pockets  = load_mask(MASK_POCKETS_PATH, (H, W))
mask_webbing  = load_mask(MASK_WEBBING_PATH, (H, W))
# Helper combined masks for quicker operations
mask_body_inds    = mask_body.astype(bool)
mask_pockets_inds = mask_pockets.astype(bool)
# Webbing untouched – no need for bool array

# Convert template to LAB once
lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
L_orig, A_orig, B_orig = cv2.split(lab)

# ---------------------------------------------------------
# Read colour combinations
# ---------------------------------------------------------
with open(CSV_COLORS, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    combos = list(reader)

print(f"Generating {len(combos)} colour-ways …")

for row in combos:
    file_base   = os.path.splitext(row['filename'].strip())[0]
    body_hex    = row['body_color'].strip()
    pockets_hex = row['pockets_color'].strip()

    # Convert to BGR & then LAB single pixel
    body_bgr        = np.array([[hex_to_bgr(body_hex)]],    dtype=np.uint8)
    pockets_bgr     = np.array([[hex_to_bgr(pockets_hex)]], dtype=np.uint8)
    body_lab        = cv2.cvtColor(body_bgr,    cv2.COLOR_BGR2LAB)[0,0]
    pockets_lab     = cv2.cvtColor(pockets_bgr, cv2.COLOR_BGR2LAB)[0,0]

    # Clone original LAB channels to work on
    L = L_orig.copy()
    A = A_orig.copy()
    B = B_orig.copy()

    # -------- Body region: change hue/sat only --------
    A[mask_body_inds] = body_lab[1]
    B[mask_body_inds] = body_lab[2]

    # -------- Pockets region: change hue/sat + darken/brighten to match --------
    A[mask_pockets_inds] = pockets_lab[1]
    B[mask_pockets_inds] = pockets_lab[2]

    # -- Hard clamp pocket lightness to target L ----------------
    pocket_L_vals = L[mask_pockets_inds]
    if pocket_L_vals.size:
        target_L = float(pockets_lab[0])          # exact L of overlay colour
        # Blend 90 % toward the target so we still keep folds
        blend = 0.9
        L[mask_pockets_inds] = np.clip(
            pocket_L_vals * (1 - blend) + target_L * blend, 0, 255
        ).astype(np.uint8)

    # -------- Merge & convert back --------
    lab_coloured = cv2.merge([L, A, B])
    out_bgr      = cv2.cvtColor(lab_coloured, cv2.COLOR_LAB2BGR)

    # -------- Save --------
    out_webp = os.path.join(OUTPUT_DIR, f"{file_base}_v2.webp")
    out_jpg  = os.path.join(OUTPUT_DIR, f"{file_base}_v2.jpg")

    cv2.imwrite(out_webp, out_bgr)
    cv2.imwrite(out_jpg,  out_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 92])

    print(f" ✔ {file_base}  (body {body_hex}, pockets {pockets_hex})")

    # ––– How many pixels are being recoloured?
    print("   body px:", int(mask_body_inds.sum()),
          "pocket px:", int(mask_pockets_inds.sum()))

    # ––– What is average LAB in pockets AFTER recolour?
    pocket_lab_now = cv2.cvtColor(out_bgr, cv2.COLOR_BGR2LAB)[mask_pockets_inds]
    Lmean, Amean, Bmean = pocket_lab_now[:,0].mean(), pocket_lab_now[:,1].mean(), pocket_lab_now[:,2].mean()
    print(f"   pocket L={Lmean:.1f}  a={Amean:.1f}  b={Bmean:.1f}")

print("Done.")
