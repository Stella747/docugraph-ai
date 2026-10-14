import json
from dataclasses import asdict
from pathlib import Path

from docugraph.ingest.pdf_parser import parse_pdf

if __name__ == "__main__":
    out = Path("data/processed")
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for pdf in sorted(Path("data/raw").glob("*.pdf")):
        secs = parse_pdf(pdf)
        rows += [asdict(s) for s in secs]
        print(f"{pdf.name}: {len(secs)} sections")
    (out / "sections.json").write_text(json.dumps(rows, indent=2))