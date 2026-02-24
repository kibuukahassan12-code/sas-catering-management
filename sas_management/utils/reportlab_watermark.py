"""ReportLab watermark helpers (SAS logo)."""

from __future__ import annotations

import os
from functools import lru_cache
from io import BytesIO
from typing import Optional, Tuple


def _find_logo_path(static_folder: Optional[str]) -> Optional[str]:
    if not static_folder:
        return None
    for fn in ("ssas_logo.png", "sas_logo.png"):
        p = os.path.join(static_folder, "images", fn)
        if os.path.exists(p):
            return p
    return None


@lru_cache(maxsize=8)
def _watermark_png_bytes(path: str, opacity: float) -> Tuple[bytes, Tuple[int, int]]:
    """
    Load image as PNG bytes with alpha applied.
    Returns (png_bytes, (w, h)).
    """
    from PIL import Image as PILImage

    img = PILImage.open(path).convert("RGBA")
    w, h = img.size

    # Apply opacity to alpha channel
    r, g, b, a = img.split()
    a = a.point(lambda p: int(p * opacity))
    img = PILImage.merge("RGBA", (r, g, b, a))

    out = BytesIO()
    img.save(out, format="PNG")
    return out.getvalue(), (w, h)


def make_center_watermark_callback(
    *,
    static_folder: Optional[str],
    opacity: float = 0.12,
    width_ratio: float = 0.40,
):
    """
    Create a ReportLab onFirstPage/onLaterPages callback that draws the SAS logo
    watermark centered on the page.
    """
    logo_path = _find_logo_path(static_folder)

    def _cb(canvas, doc):  # reportlab callback signature
        if not logo_path:
            return
        try:
            png_bytes, (w, h) = _watermark_png_bytes(logo_path, opacity)
            from reportlab.lib.utils import ImageReader

            page_w, page_h = doc.pagesize
            target_w = page_w * width_ratio
            aspect = (w / h) if h else 1.0
            target_h = target_w / aspect if aspect else target_w

            x = (page_w - target_w) / 2.0
            y = (page_h - target_h) / 2.0

            canvas.saveState()
            canvas.drawImage(
                ImageReader(BytesIO(png_bytes)),
                x,
                y,
                width=target_w,
                height=target_h,
                mask="auto",
                preserveAspectRatio=True,
                anchor="c",
            )
            canvas.restoreState()
        except Exception:
            # Never break document generation because of watermark failures.
            return

    return _cb

