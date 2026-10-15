import json
from collections import defaultdict
from pathlib import Path

from docugraph.db import connect
from docugraph.retrieval.search import search

queries = json.loads(Path("evaluation/queries_hard.json").read_text())
MODES, K = ("vector", "keyword", "hybrid"), 3
by_type = defaultdict(lambda: defaultdict(list))

with connect() as conn:
    print(f"Recall@{K}")
    print(f"{'id':4} {'type':11} {'vector':>7} {'keyword':>8} {'hybrid':>7}")
    for q in queries:
        want = {tuple(e) for e in q["expected"]}
        row = []
        for mode in MODES:
            got = {(h["document"], h["section"]) for h in search(conn, q["query"], mode, K)}
            r = len(want & got) / len(want)
            by_type[q["type"]][mode].append(r)
            row.append(r)
        print(f"{q['id']:4} {q['type']:11} " + " ".join(f"{r:7.2f}" for r in row))
    print("\nMean by query type")
    for t, modes in by_type.items():
        print(f"{t:11} " + " ".join(f"{sum(modes[m]) / len(modes[m]):7.2f}" for m in MODES))