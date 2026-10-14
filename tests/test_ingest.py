import json
from pathlib import Path

from docugraph.ingest.pdf_parser import parse_pdf


def test_every_ground_truth_reference_is_found_on_the_right_page():
    truth = json.loads(Path("evaluation/ground_truth.json").read_text())
    refs = [e for group in ("issues", "decoys")
            for item in truth[group] for e in item["evidence"]]
    parsed = {pdf.name: {s.section: s for s in parse_pdf(pdf)}
              for pdf in Path("data/raw").glob("*.pdf")}
    for r in refs:
        found = parsed[r["document"]][r["section"]]
        assert found.page == r["page"], r