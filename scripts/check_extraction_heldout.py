import json
from pathlib import Path

from docugraph.extract.extractor import ATTRS, SEVERITIES

items = json.loads(Path("evaluation/extraction_heldout.json").read_text())
problems = []
for it in items:
    if "TODO" in it["text"] or len(it["text"].split()) < 5:
        problems.append(f"{it['id']}: clause not written")
    if it["id"].startswith("X") and not it["facts"]:
        problems.append(f"{it['id']}: positive clause has no facts")
    if it["id"].startswith("N") and it["facts"]:
        problems.append(f"{it['id']}: negative clause must have facts []")
    for f in it["facts"]:
        if f.get("attribute") not in ATTRS:
            problems.append(f"{it['id']}: unknown attribute {f.get('attribute')!r}")
        if f.get("bound") not in ("max", "min", "exact"):
            problems.append(f"{it['id']}: bound must be max, min or exact")
        if f.get("severity") not in SEVERITIES:
            problems.append(f"{it['id']}: severity must be one of {SEVERITIES}")
        if not isinstance(f.get("value"), str):
            problems.append(f"{it['id']}: value must be a string, e.g. \"24\"")
print("\n".join(problems) if problems else f"OK: {len(items)} clauses valid")