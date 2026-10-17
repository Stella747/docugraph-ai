import json
import time
from pathlib import Path

from docugraph.agents.report_graph import build

findings = json.loads(Path("data/processed/findings.json").read_text())
t0 = time.perf_counter()
final = build().invoke({"findings": findings, "index": 0, "reports": [], "feedback": "", "attempts": 0},
                       {"recursion_limit": 100})
reports = final["reports"]
Path("data/processed/report.json").write_text(json.dumps(reports, indent=2))

order = {"High": 0, "Medium": 1, "Low": 2}
lines = ["# DocuGraph compliance report", ""]
for i, r in enumerate(sorted(reports, key=lambda r: order[r["severity"]]), 1):
    tag = "" if r["verified"] else "  (UNVERIFIED: template text, model output was rejected)"
    lines += [f"## {i}. {r['attribute']}: {r['severity']} risk{tag}", "", r["explanation"], "",
              f"**Recommended action:** {r['recommended_action']}", "", "**Evidence**"]
    lines += [f"- {e['document']}, section {e['section']}, page {e['page']}: \"{e['text']}\"" for e in r["evidence"]]
    lines.append("")
Path("data/processed/report.md").write_text("\n".join(lines))

ok = sum(r["verified"] for r in reports)
first_try = sum(r["verified"] and r["attempts"] == 1 for r in reports)
print(f"{len(reports)} findings reported in {time.perf_counter() - t0:.0f}s")
print(f"verified: {ok}/{len(reports)}   verified on first attempt: {first_try}/{len(reports)}   fallback: {len(reports) - ok}")