"""Stage 4 — visualization.

Turns a decoded page into an inline data URI for QC display. Pure transformation
(SRP: it only renders); no port needed. The preview is JPEG-compressed and
size-capped so the result page stays light even for multi-page PDFs — the stored
<id>_p<N>_original.png remains the lossless source of truth.
"""

import base64
import io

from PIL import Image

from app.domain.models import LoadedImage


def to_data_uri(page: LoadedImage, max_dim: int = 1000, quality: int = 85) -> str:
    img = Image.fromarray(page.rgb, mode="RGB")

    longest = max(img.width, img.height)
    if longest > max_dim:  # downscale for on-screen preview only
        scale = max_dim / longest
        img = img.resize((int(img.width * scale), int(img.height * scale)))

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=quality)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"
