import cv2
import numpy as np
import pymupdf


def page_to_bgr(page: pymupdf.Page, dpi: int = 150) -> np.ndarray:
    pix = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csRGB)
    img = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, 3)
    return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)


def clean_binarize(img_bgr: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.fastNlMeansDenoising(gray, None, h=15, templateWindowSize=7, searchWindowSize=21)
    _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return cv2.cvtColor(bw, cv2.COLOR_GRAY2BGR)


def table_line_counts(clean_bgr: np.ndarray) -> tuple[int, int]:
    gray = cv2.cvtColor(clean_bgr, cv2.COLOR_BGR2GRAY)
    inv = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    h, w = inv.shape
    horiz = cv2.morphologyEx(inv, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (w // 8, 1)))
    vert = cv2.morphologyEx(inv, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, h // 40)))
    return cv2.connectedComponents(horiz)[0] - 1, cv2.connectedComponents(vert)[0] - 1


def has_table_structure(clean_bgr: np.ndarray) -> bool:
    n_h, n_v = table_line_counts(clean_bgr)
    return n_h >= 3 and n_v >= 2


def estimate_skew(clean_bgr: np.ndarray) -> float:
    """Median angle (degrees) of long near-horizontal lines; 0.0 if none found."""
    gray = cv2.cvtColor(clean_bgr, cv2.COLOR_BGR2GRAY)
    inv = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    w = inv.shape[1]
    lines = cv2.HoughLinesP(inv, 1, np.pi / 1440, threshold=150, minLineLength=w // 4, maxLineGap=15)
    if lines is None:
        return 0.0
    segments = lines.reshape(-1, 4)
    angles = [np.degrees(np.arctan2(y2 - y1, x2 - x1)) for x1, y1, x2, y2 in segments]
    angles = [a for a in angles if abs(a) < 10]
    return float(np.median(angles)) if angles else 0.0


def deskew(clean_bgr: np.ndarray) -> np.ndarray:
    angle = estimate_skew(clean_bgr)
    if abs(angle) < 0.2:
        return clean_bgr
    h, w = clean_bgr.shape[:2]
    m = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    return cv2.warpAffine(clean_bgr, m, (w, h), borderValue=(255, 255, 255))