from pathlib import Path
import pytest

from docugraph.ingest.pdf_parser import parse_pdf

@pytest.mark.slow
def test_degraded_scanned_sla_table_is_recovered():
    path = Path("data/scans/variants/sla_tilt_blur_noise.pdf")
    sections = {s.section: s for s in parse_pdf(path)}
    assert "| Critical | 8 hours | 24 hours |" in sections["1.1"].text