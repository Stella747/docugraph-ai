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


def parse_pdf(path: Path) -> list[Section]:
    sections: list[Section] = []
    current: Section | None = None
    with pymupdf.open(path) as doc:
        for page in doc:
            for block in page.get_text("dict")["blocks"]:
                for line in block.get("lines", []):
                    spans = line["spans"]
                    text = "".join(s["text"] for s in spans).strip()
                    if not text:
                        continue
                    bold = all("Bold" in s["font"] for s in spans)
                    size = max(s["size"] for s in spans)
                    if bold and size > 13:  # document title
                        continue
                    match = HEADING_RE.match(text)
                    if bold and match:
                        current = Section(path.name, page.number + 1,
                                          match.group(1), match.group(2), "")
                        sections.append(current)
                    elif current:
                        current.text = f"{current.text} {text}".strip()
    return sections