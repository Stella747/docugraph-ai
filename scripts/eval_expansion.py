import json
from collections import defaultdict
from pathlib import Path

from docugraph.agents.ask import expand
from docugraph.db import connect
from docugraph.retrieval.search import search

queries = []
for name in ("queries_hard.json", "queries_heldout.json"):
    queries += json.loads(Path("evaluation", name).read_text())

stats = defaultdict(lambda: {"base": [], "expanded": [], "size": []})
with connect() as conn:
    for q in queries:
        want = {tuple(e) for e in q["expected"]}
        keys = [(h["document"], h["section"]) for h in search(conn, q["query"], "hybrid_rerank", 3)]
        expanded, _ = expand(keys)
        s = stats[q["type"]]
        s["base"].append(len(want & set(keys)) / len(want))
        s["expanded"].append(len(want & set(expanded)) / len(want))
        s["size"].append(len(expanded))

print(f"{'type':11} {'n':>3} {'retrieval':>10} {'+expansion':>11} {'avg clauses':>12}")
for t, s in stats.items():
    n = len(s["base"])
    print(f"{t:11} {n:3} {sum(s['base']) / n:10.2f} {sum(s['expanded']) / n:11.2f} {sum(s['size']) / n:12.1f}")