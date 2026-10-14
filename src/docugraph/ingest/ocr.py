import cv2
import numpy as np
import pymupdf
from rapidocr import RapidOCR

_engine = None


def ocr_page_lines(page: pymupdf.Page, dpi: int = 200) -> list[str]:
    global _engine
    if _engine is None:
        _engine = RapidOCR()
    pix = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csRGB)
    img = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, 3)
    result = _engine(cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    if result.txts is None:
        return []
    items = sorted(zip(result.boxes, result.txts), key=lambda bt: bt[0][0][1])  # top-to-bottom
    return [t.strip() for _, t in items if t.strip()]