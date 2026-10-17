import json
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas

RAW = Path("data/raw")
EVAL = Path("evaluation")

DOCS = {
    "b_services_agreement.pdf": ("Master Services Agreement - Vertex Systems Ltd and Aegis Financial", [
        ("2.1", "Term", "This Agreement shall commence on March 1, 2027 and shall remain in effect for 34 months, terminating on December 31, 2029."),
        ("5.2", "Critical Response", "For Critical operational incidents, Vendor shall acknowledge and respond within a time window not to be exceeded by 6 hours."),
        ("5.3", "Priority 1 Resolution", "Vendor shall fully resolve all Priority 1 incidents within 12 hours of initial triage."),
        ("6.1", "Breach Notification", "Vendor shall notify Customer of any confirmed personal data breach within 96 hours of becoming aware of the event."),
        ("7.2", "Insurance", "Vendor shall maintain cyber liability insurance coverage of not less than USD 3,500,000 throughout the active term."),
        ("8.1", "Payment", "Customer shall remit payment for undisputed invoices within 60 days of invoice receipt (Net 60)."),
    ]),
    "b_support_schedule.pdf": ("Schedule B - Service Level Targets - Vertex Systems Ltd", [
        ("1.1", "Support Targets", "Response and resolution targets by incident severity level are set out in the table below."),
    ]),
    "b_security_policy.pdf": ("Aegis Financial - Third-Party Vendor Security Policy v4.0", [
        ("3.1", "Critical Response", "Vendors must respond to Critical security and operational incidents within 2 hours of initial detection."),
        ("3.2", "Critical Resolution", "Vendors shall achieve complete resolution for Critical incidents within 8 hours."),
        ("3.3", "High Response", "Vendors must respond to High severity incidents within a maximum period of 4 hours."),
        ("3.4", "High Resolution", "Resolution targets for High severity incidents must be completed within 12 hours."),
        ("3.5", "Medium Response", "Vendors must respond to Medium severity incidents within 24 hours."),
        ("4.1", "Breach Notification", "In the event of a personal data breach, Vendor shall report the incident to Aegis Financial within 24 hours."),
        ("4.4", "Insurance", "Third-party vendors processing customer data must maintain a floor of USD 6,000,000 in general cyber liability insurance."),
    ]),
    "b_privacy_regulation_excerpt.pdf": ("Digital Personal Data Protection Regulation 2026 - Excerpt", [
        ("9", "Breach Reporting", "A data processor must report any security compromise of personal data to the Supervisory Authority within 12 hours of awareness."),
    ]),
    "b_insurance_certificate.pdf": ("Certificate of Insurance - Vertex Systems Ltd", [
        ("1.1", "Coverage", "Cyber liability insurance limit: USD 3,500,000 per claim and in the aggregate."),
        ("2.1", "Policy Period", "Policy period: 1 April 2027 to March 31, 2028. Coverage terminates at expiration unless renewed."),
    ]),
    "b_invoice.pdf": ("Invoice 8810 - Vertex Systems Ltd", [
        ("1", "Invoice Details", "Invoice date: 15 April 2027. Total amount due: USD 64,500 for enterprise software licenses."),
        ("2", "Payment Terms", "Payment is strictly due within 15 days of the invoice date (Net 15)."),
    ]),
}

TABLES = {
    ("b_support_schedule.pdf", "1.1"): [
        ["Severity", "Response time", "Resolution target"],
        ["High", "3 hours", "10 hours"],
        ["Medium", "12 hours", "48 hours"],
    ],
}

FILLER_TEXT = ("This section is included for administrative completeness and does not alter any other "
               "provision. Headings are for reference only and notices are governed by the schedule of definitions.")
FILLER_COUNT = {"b_services_agreement.pdf": 12, "b_security_policy.pdf": 18, "b_privacy_regulation_excerpt.pdf": 8}

# issue id -> (type, severity, evidence clauses). B6 is the stress case: expected to be missed.
ISSUES = {
    "ISS-B1": ("response_mismatch", "High", [("b_services_agreement.pdf", "5.2"), ("b_security_policy.pdf", "3.1")]),
    "ISS-B2": ("breach_notice_mismatch", "High", [("b_services_agreement.pdf", "6.1"), ("b_security_policy.pdf", "4.1"), ("b_privacy_regulation_excerpt.pdf", "9")]),
    "ISS-B3": ("insurance_shortfall", "Medium", [("b_services_agreement.pdf", "7.2"), ("b_insurance_certificate.pdf", "1.1"), ("b_security_policy.pdf", "4.4")]),
    "ISS-B4": ("insurance_expiry", "Medium", [("b_insurance_certificate.pdf", "2.1"), ("b_services_agreement.pdf", "2.1")]),
    "ISS-B5": ("payment_terms_mismatch", "Low", [("b_invoice.pdf", "2"), ("b_services_agreement.pdf", "8.1")]),
    "ISS-B6": ("priority1_vs_critical", "High", [("b_services_agreement.pdf", "5.3"), ("b_security_policy.pdf", "3.2")]),
}
DECOYS = {  # compliant pairs: the schedule table beats the policy; a finding here is a false alarm
    "DEC-B1": ("compliant_high_response", [("b_support_schedule.pdf", "1.1"), ("b_security_policy.pdf", "3.3")]),
    "DEC-B2": ("compliant_high_resolution", [("b_support_schedule.pdf", "1.1"), ("b_security_policy.pdf", "3.4")]),
    "DEC-B3": ("compliant_medium_response", [("b_support_schedule.pdf", "1.1"), ("b_security_policy.pdf", "3.5")]),
}
A_TOKENS = ["Acme", "Northwind", "2,000,000", "5,000,000", "72 hours", "Net 45", "Net 30"]


def todo_left():
    left = [f"{f} {n}" for f, (_, secs) in DOCS.items() for n, _, txt in secs if "TODO" in txt]
    left += [f"{f} title" for f, (t, _) in DOCS.items() if "TODO" in t]
    left += [f"{f} table" for (f, _), rows in TABLES.items() if any("TODO" in c for r in rows for c in r)]
    return left


def render(filename, title, sections, page_index):
    c = canvas.Canvas(str(RAW / filename), pagesize=A4)
    w, h = A4
    margin, y, page = 56, h - 56, 1
    c.setFont("Helvetica-Bold", 15)
    c.drawString(margin, y, title)
    y -= 36
    for num, heading, text in sections:
        rows = TABLES.get((filename, num))
        lines = simpleSplit(text, "Helvetica", 11, w - 2 * margin)
        need = 24 + 15 * len(lines) + (20 * len(rows) + 14 if rows else 0)
        if y - need < margin:
            c.showPage()
            page, y = page + 1, h - margin
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin, y, f"{num}  {heading}")
        y -= 20
        c.setFont("Helvetica", 11)
        for line in lines:
            c.drawString(margin, y, line)
            y -= 15
        if rows:
            col_w = (w - 2 * margin) / len(rows[0])
            xs = [margin + i * col_w for i in range(len(rows[0]) + 1)]
            ys = [y - 4 - 20 * i for i in range(len(rows) + 1)]
            c.grid(xs, ys)
            for r, row in enumerate(rows):
                c.setFont("Helvetica-Bold" if r == 0 else "Helvetica", 10)
                for ci, cell in enumerate(row):
                    c.drawString(xs[ci] + 6, ys[r] - 14, cell)
            y = ys[-1] - 14
        y -= 10
        page_index[(filename, num)] = page
    c.save()


def ref(idx, f, s):
    return {"document": f, "section": s, "page": idx[(f, s)]}


if __name__ == "__main__":
    left = todo_left()
    if left:
        raise SystemExit("Still TODO:\n  " + "\n  ".join(left))
    RAW.mkdir(parents=True, exist_ok=True)
    EVAL.mkdir(exist_ok=True)
    idx = {}
    for fname, (title, secs) in DOCS.items():
        filler = [(f"0.{i}", "General Provisions", FILLER_TEXT) for i in range(1, FILLER_COUNT.get(fname, 0) + 1)]
        render(fname, title, filler + secs, idx)
        text = title + " ".join(t for _, _, t in secs)
        for tok in A_TOKENS:
            if tok in text:
                print(f"WARNING: {fname} reuses corpus A token {tok!r}")
    truth = {
        "issues": [{"id": i, "type": t, "severity": s, "evidence": [ref(idx, f, sec) for f, sec in ev]}
                   for i, (t, s, ev) in ISSUES.items()],
        "decoys": [{"id": i, "type": t, "evidence": [ref(idx, f, sec) for f, sec in ev]}
                   for i, (t, ev) in DECOYS.items()],
    }
    (EVAL / "ground_truth.json").write_text(json.dumps(truth, indent=2))
    print(f"Generated {len(DOCS)} PDFs in {RAW} and evaluation/ground_truth.json")