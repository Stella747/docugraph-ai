import json
from pathlib import Path

from docugraph.db import connect
from docugraph.retrieval.search import search

truth = json.loads(Path("evaluation/ground_truth.json").read_text())
evidence = {i["id"]: {(e["document"], e["section"]) for e in i["evidence"]}
            for group in ("issues", "decoys") for i in truth[group]}
queries = json.loads(Path("evaluation/queries.json").read_text())

with connect() as conn:
    for k in (3, 5):
        print(f"\nRecall@{k}")
        print(f"{'query':8} {'vector':>8} {'keyword':>8} {'hybrid':>8}")
        totals = {"vector": 0.0, "keyword": 0.0, "hybrid": 0.0}
        for qid, q in queries.items():
            row = []
            for mode in totals:
                hits = {(h["document"], h["section"]) for h in search(conn, q, mode, k)}
                recall = len(evidence[qid] & hits) / len(evidence[qid])
                totals[mode] += recall
                row.append(recall)
            print(f"{qid:8} " + " ".join(f"{r:8.2f}" for r in row))
        print(f"{'MEAN':8} " + " ".join(f"{t / len(queries):8.2f}" for t in totals.values()))