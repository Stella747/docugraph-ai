from pathlib import Path

from docugraph.ingest.pdf_parser import parse_pdf


def test_sla_table_keeps_row_structure():
    sections = {s.section: s for s in parse_pdf(Path("data/raw/acme_sla_schedule.pdf"))}
    assert "| Critical | 8 hours | 24 hours |" in sections["1.1"].text