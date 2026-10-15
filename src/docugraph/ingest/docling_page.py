import tempfile
from pathlib import Path

import cv2
import numpy as np
import pymupdf

_converter = None


def docling_markdown(clean_bgr: np.ndarray) -> str:
    """Run Docling on one preprocessed page image and return Markdown."""
    global _converter
    if _converter is None:  # load the heavy models once, not per page
        from docling.document_converter import DocumentConverter
        _converter = DocumentConverter()
    with tempfile.TemporaryDirectory() as tmp:
        pdf_path = Path(tmp) / "page.pdf"
        h, w = clean_bgr.shape[:2]
        doc = pymupdf.open()
        page = doc.new_page(width=w * 72 / 150, height=h * 72 / 150)
        page.insert_image(page.rect, stream=cv2.imencode(".png", clean_bgr)[1].tobytes())
        doc.save(pdf_path)
        doc.close()
        return _converter.convert(str(pdf_path)).document.export_to_markdown()