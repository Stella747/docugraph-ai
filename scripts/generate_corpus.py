import json
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas

RAW = Path("data/raw")
EVAL = Path("evaluation")
RAW.mkdir(parents=True, exist_ok=True)
EVAL.mkdir(exist_ok=True)

# filename -> (title, [(section_number, heading, text), ...])
DOCS = {
    "acme_cloud_msa.pdf": ("Master Services Agreement - Acme Cloud Ltd and Northwind Retail", [
        ("4.2", "Term", "This Agreement is effective 1 January 2026 and continues for 24 months, ending 31 December 2027."),
        ("8.2", "Incident Response", "Vendor shall respond to Critical incidents within 4 hours of notification."),
        ("9.1", "Breach Notification", "Vendor shall notify Customer of any personal data breach within 72 hours of becoming aware of it."),
        ("10.4", "Access Reviews", "Vendor shall review privileged access to Customer systems quarterly."),
        ("11.3", "Payment Terms", "Customer shall pay undisputed invoices within 45 days of the invoice date (Net 45)."),
        ("12.1", "Insurance", "Vendor shall maintain cyber liability insurance of not less than USD 2,000,000 throughout the Term."),
    ]),
    "northwind_vendor_security_policy.pdf": ("Northwind Retail - Third-Party Security Policy v3.1", [
        ("4.1", "Critical Incident Response", "All vendors must respond to Critical incidents within 2 hours of notification."),
        ("5.3", "Breach Notification", "Vendors must notify Northwind of any personal data breach within 24 hours of becoming aware of it."),
        ("6.2", "Insurance Requirements", "Vendors handling customer data must hold cyber liability insurance of at least USD 5,000,000."),
        ("7.1", "Access Reviews", "Privileged vendor access must be reviewed at least quarterly."),
    ]),
    "fictional_data_protection_act_excerpt.pdf": ("Fictional Data Protection Act 2025 - Excerpt", [
        ("12", "Breach Reporting", "A data controller must report a personal data breach to the Authority within 24 hours of becoming aware of it."),
    ]),
    "acme_insurance_certificate.pdf": ("Certificate of Insurance - Acme Cloud Ltd", [
        ("1.1", "Coverage", "Cyber liability coverage limit: USD 2,000,000 per claim."),
        ("2.1", "Policy Period", "Policy period: 1 July 2025 to 30 June 2026. Coverage ends at expiry unless renewed."),
    ]),
    "acme_invoice_0412.pdf": ("Invoice 0412 - Acme Cloud Ltd", [
        ("1", "Invoice Details", "Invoice date: 1 March 2026. Amount due: USD 48,200 for cloud services, February 2026."),
        ("3", "Payment Terms", "Payment is due within 30 days of the invoice date (Net 30)."),
    ]),
        "acme_sla_schedule.pdf": ("Schedule A - Service Levels - Acme Cloud Ltd", [
        ("1.1", "Response Times", "Response and resolution targets by incident severity are set out in the table below."),
    ]),
}

FILLER_TEXT = (
    "The parties acknowledge that this clause is included for general administrative purposes "
    "and does not modify any other provision of this document. Interpretation, headings and "
    "notices are governed by the definitions schedule."
)
FILLER_COUNT = {
    "acme_cloud_msa.pdf": 14,
    "northwind_vendor_security_policy.pdf": 22,
    "fictional_data_protection_act_excerpt.pdf": 10,
}

# issue id -> (type, severity, [(file, section), ...])
ISSUES = {
    "ISS-001": ("sla_mismatch", "High", [("acme_cloud_msa.pdf", "8.2"), ("northwind_vendor_security_policy.pdf", "4.1")]),
    "ISS-002": ("breach_notice_mismatch", "High", [("acme_cloud_msa.pdf", "9.1"), ("northwind_vendor_security_policy.pdf", "5.3"), ("fictional_data_protection_act_excerpt.pdf", "12")]),
    "ISS-003": ("insurance_shortfall", "Medium", [("acme_cloud_msa.pdf", "12.1"), ("acme_insurance_certificate.pdf", "1.1"), ("northwind_vendor_security_policy.pdf", "6.2")]),
    "ISS-004": ("insurance_expiry", "Medium", [("acme_insurance_certificate.pdf", "2.1"), ("acme_cloud_msa.pdf", "4.2")]),
    "ISS-005": ("payment_terms_mismatch", "Low", [("acme_invoice_0412.pdf", "3"), ("acme_cloud_msa.pdf", "11.3")]),
}
DECOYS = {"DEC-001": ("consistent_access_review", [("acme_cloud_msa.pdf", "10.4"), ("northwind_vendor_security_policy.pdf", "7.1")])}

TABLES = {
    ("acme_sla_schedule.pdf", "1.1"): [
        ["Severity", "Response time", "Resolution target"],
        ["Critical", "8 hours", "24 hours"],
        ["High", "12 hours", "48 hours"],
        ["Medium", "2 business days", "5 business days"],
    ],
}
ISSUES["ISS-006"] = ("sla_internal_inconsistency", "High",
                     [("acme_sla_schedule.pdf", "1.1"), ("acme_cloud_msa.pdf", "8.2")])

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

def ref(page_index, f, s):
    return {"document": f, "section": s, "page": page_index[(f, s)]}


if __name__ == "__main__":
    idx = {}
    for fname, (title, secs) in DOCS.items():
        filler= [(f"0.{1}","General Provisions", FILLER_TEXT)
                 for i in range(1, FILLER_COUNT.get(fname,0)+1)]
        render(fname, title, filler + secs, idx)
    truth = {
        "issues": [
            {"id": i, "type": t, "severity": sev, "evidence": [ref(idx, f, s) for f, s in ev]}
            for i, (t, sev, ev) in ISSUES.items()
        ],
        "decoys": [
            {"id": i, "type": t, "evidence": [ref(idx, f, s) for f, s in ev]}
            for i, (t, ev) in DECOYS.items()
        ],
    }
    (EVAL / "ground_truth.json").write_text(json.dumps(truth, indent=2))
    print(f"Generated {len(DOCS)} PDFs in {RAW} and evaluation/ground_truth.json")