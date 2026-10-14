import re
from dataclasses import dataclass
from pathlib import Path

import pymupdf

HEADING_RE = re.compile(r"^(\d+(?:\.\d+)*)\s+(.+)$")


@dataclass
class Section:
    document: str
    page: int
    section: str
    heading: str
    text: str


@dataclass
class Line:
    page: int
    text: str
    is_heading: bool


def _looks_like_heading(text: str) -> bool:
    """OCR has no font info, so use text shape: short, capitalised, no final period."""
    m = HEADING_RE.match(text)
    if not m:
        return False
    words = m.group(2).split()
    return len(words) <= 6 and words[0][0].isupper() and not text.endswith(".")


def _digital_lines(page: pymupdf.Page) -> list[Line]:
    out = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            spans = line["spans"]
            text = "".join(s["text"] for s in spans).strip()
            if not text:
                continue
            bold = all("Bold" in s["font"] for s in spans)
            if bold and max(s["size"] for s in spans) > 13:  # document title
                continue
            out.append(Line(page.number + 1, text, bold and bool(HEADING_RE.match(text))))
    return out


def _ocr_lines(page: pymupdf.Page) -> list[Line]:
    from docugraph.ingest.ocr import ocr_page_lines  # lazy: only load OCR models if needed

    return [Line(page.number + 1, t, _looks_like_heading(t)) for t in ocr_page_lines(page)]


def parse_pdf(path: Path) -> list[Section]:
    lines: list[Line] = []
    with pymupdf.open(path) as doc:
        for page in doc:
            has_text_layer = bool(page.get_text().strip())
            lines += _digital_lines(page) if has_text_layer else _ocr_lines(page)

    sections: list[Section] = []
    current: Section | None = None
    for ln in lines:
        m = HEADING_RE.match(ln.text)
        if ln.is_heading and m:
            current = Section(path.name, ln.page, m.group(1), m.group(2), "")
            sections.append(current)
        elif current:
            current.text = f"{current.text} {ln.text}".strip()
    return sections