from pathlib import Path

import cv2
import numpy as np
import pymupdf

SRC, DST = Path("data/raw"), Path("data/scans")
SCAN_FILES = ["acme_insurance_certificate.pdf", "acme_invoice_0412.pdf"]
rng = np.random.default_rng(42)


def degrade(img, angle=6, noise_sigma=40):
    h, w = img.shape[:2]
    m = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    img = cv2.warpAffine(img, m, (w, h), borderValue=(255, 255, 255))
    img = cv2.GaussianBlur(img, (3, 3), 0)
    return np.clip(img + rng.normal(0, noise_sigma, img.shape), 0, 255).astype(np.uint8)


if __name__ == "__main__":
    DST.mkdir(parents=True, exist_ok=True)
    for name in SCAN_FILES:
        out = pymupdf.open()
        with pymupdf.open(SRC / name) as doc:
            for page in doc:
                pix = page.get_pixmap(dpi=150, colorspace=pymupdf.csRGB)
                img = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, 3)
                ok, png = cv2.imencode(".png", cv2.cvtColor(degrade(img), cv2.COLOR_RGB2BGR))
                p = out.new_page(width=page.rect.width, height=page.rect.height)
                p.insert_image(p.rect, stream=png.tobytes())
        out.save(DST / name)
        print("wrote", DST / name)