import sys
from pathlib import Path

import cv2
import numpy as np
import pymupdf


def clean(img_bgr, binarize):
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.fastNlMeansDenoising(gray, None, h=15, templateWindowSize=7, searchWindowSize=21)
    if binarize:
        _, gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)


src = Path(sys.argv[1])
for mode, binarize in (("denoised", False), ("binarized", True)):
    out = pymupdf.open()
    with pymupdf.open(src) as doc:
        for page in doc:
            pix = page.get_pixmap(dpi=150, colorspace=pymupdf.csRGB)
            img = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, 3)
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            ok, png = cv2.imencode(".png", clean(img, binarize))
            p = out.new_page(width=page.rect.width, height=page.rect.height)
            p.insert_image(p.rect, stream=png.tobytes())
    dst = src.with_name(f"{src.stem}_{mode}.pdf")
    out.save(dst)
    print("wrote", dst)