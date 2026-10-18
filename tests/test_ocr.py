from difflib import SequenceMatcher
from pathlib import Path
import pytest

from docugraph.ingest.pdf_parser import parse_pdf

SCANNED = ["acme_insurance_certificate.pdf", "acme_invoice_0412.pdf"]

@pytest.mark.slow
def test_scanned_docs_match_digital_originals():
    for name in SCANNED:
        digital = {s.section: s for s in parse_pdf(Path("data/raw") / name)}
        scanned = {s.section: s for s in parse_pdf(Path("data/scans") / name)}
        assert digital.keys() == scanned.keys(), name
        for key, d in digital.items():
            ratio = SequenceMatcher(None, d.text, scanned[key].text).ratio()
            assert scanned[key].page == d.page
            assert ratio > 0.95, (name, key, ratio)