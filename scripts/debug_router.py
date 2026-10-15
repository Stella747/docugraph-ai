from pathlib import Path

import pymupdf

from docugraph.ingest.preprocess import (clean_binarize, deskew, estimate_skew,
                                         page_to_bgr, table_line_counts)

for name in ["variants/sla_clean.pdf", "variants/sla_tilt_blur_noise.pdf"]:
    with pymupdf.open(Path("data/scans") / name) as doc:
        cleaned = clean_binarize(page_to_bgr(doc[0]))
    print(name)
    print("  skew angle estimate :", round(estimate_skew(cleaned), 2))
    print("  lines (h, v) before :", table_line_counts(cleaned))
    print("  lines (h, v) after  :", table_line_counts(deskew(cleaned)))