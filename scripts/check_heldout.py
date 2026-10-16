import json
from pathlib import Path

queries = json.loads(Path("evaluation/queries_heldout.json").read_text())
sections = {(s["document"], s["section"]) for s in json.loads(Path("data/processed/sections.json").read_text())}

problems = []
for q in queries:
    qid = q["id"]
    if "TODO" in q["query"] or len(q["query"].split()) < 2:
        problems.append(f"{qid}: query not written")
    if not q["expected"]:
        problems.append(f"{qid}: no expected clauses")
    docs = set()
    for entry in q["expected"]:
        if not (isinstance(entry, list) and len(entry) == 2 and all(isinstance(x, str) for x in entry)):
            problems.append(f'{qid}: bad entry {entry!r}; each one must look like ["file.pdf", "9.1"], inside an outer list')
            continue
        doc, sec = entry
        docs.add(doc)
        if (doc, sec) not in sections:
            problems.append(f"{qid}: ({doc}, {sec}) is not a real clause")
    if q["type"] == "multihop" and len(docs) < 2:
        problems.append(f"{qid}: multihop needs clauses from 2+ documents")

print("\n".join(problems) if problems else f"OK: {len(queries)} queries valid")
raise SystemExit(1 if problems else 0)