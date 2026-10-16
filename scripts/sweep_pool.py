import json
from collections import defaultdict
from pathlib import Path

from docugraph.db import connect
from docugraph.retrieval.search import search

queries = json.loads(Path("evaluation/queries_hard.json").read_text())
K = 3
TYPES = ["paraphrase", "exact", "table", "multihop"]


def mean_recall(conn, mode, pool):
    by_type = defaultdict(list)
    for q in queries:
        want = {tuple(e) for e in q["expected"]}
        got = {(h["document"], h["section"]) for h in search(conn, q["query"], mode, K, pool)}
        by_type[q["type"]].append(len(want & got) / len(want))
    return {t: sum(v) / len(v) for t, v in by_type.items()}


CONFIGS = [("vector", 20), ("bm25", 20), ("hybrid_bm25", 3),
           ("vector_rerank", 20), ("hybrid_rerank", 10), ("hybrid_rerank", 20)]

with connect() as conn:
    print(f"{'config':20}" + "".join(f"{t:>12}" for t in TYPES))
    for mode, pool in CONFIGS:
        r = mean_recall(conn, mode, pool)
        label = f"{mode} pool={pool}"
        print(f"{label:20}" + "".join(f"{r[t]:12.2f}" for t in TYPES), flush=True)