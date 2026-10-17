import json
import sys
import time
from pathlib import Path

from docugraph.agents.ask import SECTIONS, ask
from docugraph.db import connect

items = json.loads(Path("evaluation/ask_eval.json").read_text())
problems = []
for it in items:
    if "TODO" in it["question"]:
        problems.append(f"{it['id']}: question not written")
    if it["answerable"] and not it["expected"]:
        problems.append(f"{it['id']}: answerable question needs expected clauses")
    if not it["answerable"] and it["expected"]:
        problems.append(f"{it['id']}: unanswerable question must have expected []")
    for e in it["expected"]:
        if not (isinstance(e, list) and len(e) == 2 and tuple(e) in SECTIONS):
            problems.append(f"{it['id']}: bad or unknown clause {e!r}")
if problems:
    raise SystemExit("\n".join(problems))

expand = "noexpand" not in sys.argv
rows = []
with connect() as conn:
    for it in items:
        t0 = time.perf_counter()
        r = ask(conn, it["question"], expand_graph=expand)
        dt = time.perf_counter() - t0
        cited = {(c["document"], c["section"]) for c in r["citations"]}
        want = {tuple(e) for e in it["expected"]}
        cov = len(want & cited) / len(want) if want and r["found"] else None
        rows.append({"answerable": it["answerable"], "found": r["found"], "cov": cov,
                     "checks": r["checks_passed"], "source": r["source"], "dt": dt})
        print(f"{it['id']:3} answerable={it['answerable']!s:5} answered={r['found']!s:5} "
              f"cited_expected={'-' if cov is None else f'{cov:.2f}'} "
              f"checks_passed={r['checks_passed']} source={r['source']} {dt:4.0f}s", flush=True)

ans = [r for r in rows if r["answerable"]]
una = [r for r in rows if not r["answerable"]]
covs = [r["cov"] for r in ans if r["cov"] is not None]
print(f"\nexpansion: {expand}")
print(f"answerable questions answered:   {sum(r['found'] for r in ans)}/{len(ans)}")
print(f"unanswerable correctly refused:  {sum(not r['found'] for r in una)}/{len(una)}")
print(f"expected clauses cited (answered answerable): {sum(covs) / len(covs):.2f}" if covs else "no answered questions")
print(f"answers by source: model={sum(r['source'] == 'model' for r in rows)} "
      f"rules={sum(r['source'] == 'rules' for r in rows)} none={sum(r['source'] == 'none' for r in rows)}")
print(f"checks passed: {sum(r['checks'] for r in rows)}/{len(rows)}   avg {sum(r['dt'] for r in rows) / len(rows):.0f}s per question")