from pathlib import Path

import cv2
import numpy as np
import pymupdf

SRC = Path("data/raw/acme_sla_schedule.pdf")
DST = Path("data/scans/variants")
DST.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(42)

VARIANTS = {
    "clean": (0, 0, False),
    "tilt_only": (1.5, 0, False),
    "blur_only": (0, 0, True),
    "noise_only": (0, 12, False),
    "tilt_blur_noise": (1.5, 12, True),
}

for name, (angle, sigma, blur) in VARIANTS.items():
    out = pymupdf.open()
    with pymupdf.open(SRC) as doc:
        for page in doc:
            pix = page.get_pixmap(dpi=150, colorspace=pymupdf.csRGB)
            img = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, 3).copy()
            h, w = img.shape[:2]
            if angle:
                m = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
                img = cv2.warpAffine(img, m, (w, h), borderValue=(255, 255, 255))
            if blur:
                img = cv2.GaussianBlur(img, (3, 3), 0)
            if sigma:
                img = np.clip(img + rng.normal(0, sigma, img.shape), 0, 255).astype(np.uint8)
            ok, png = cv2.imencode(".png", cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
            p = out.new_page(width=page.rect.width, height=page.rect.height)
            p.insert_image(p.rect, stream=png.tobytes())
    out.save(DST / f"sla_{name}.pdf")
    print("wrote", name)