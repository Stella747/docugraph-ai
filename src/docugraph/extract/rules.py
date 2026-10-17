import re

SEVERITY_WORDS = ["critical", "high", "medium", "low"]


def severity_from_text(text: str) -> str:
    found = {w for w in SEVERITY_WORDS if re.search(rf"\b{w}\b", text.lower())}
    return found.pop() if len(found) == 1 else "none"


def table_facts(text: str) -> list[dict]:
    """Parse a Markdown table embedded in a clause into incident response/resolution facts (hours only)."""
    rows = []
    for line in text.splitlines():
        if "|" not in line:
            continue
        cells = [c.strip() for c in line[line.index("|"):].strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-+:?", c) for c in cells):
            continue  # separator row
        rows.append(cells)
    if len(rows) < 2:
        return []
    cols = {}
    for i, h in enumerate(rows[0]):
        if "response" in h.lower():
            cols[i] = "incident_response_hours"
        elif "resolution" in h.lower():
            cols[i] = "incident_resolution_hours"
    facts = []
    for row in rows[1:]:
        sev = row[0].lower()
        if sev not in SEVERITY_WORDS:
            continue
        for i, attr in cols.items():
            m = re.fullmatch(r"(\d+)\s*hours?", row[i].lower()) if i < len(row) else None
            if m:  # targets are treated as maximums
                facts.append({"attribute": attr, "value": m.group(1), "unit": "hours",
                              "bound": "max", "severity": sev})
    return facts