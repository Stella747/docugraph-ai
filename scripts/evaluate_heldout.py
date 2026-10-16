import json
import time
from collections import defaultdict
from pathlib import Path

from docugraph.db import connect
from docugraph.retrieval.search import search

queries = json.loads(Path("evaluation/queries_heldout.json").read_text())
K, POOL = 3, 20
CONFIGS = ["vector", "bm25", "hybrid_rerank"]
TYPES = sorted({q["type"] for q in queries})

with connect() as conn:
    for mode in CONFIGS:  # warm-up so model loading isn't counted as latency
        search(conn, "warm up", mode, K, POOL)
    by_type = {m: defaultdict(list) for m in CONFIGS}
    latency = {m: [] for m in CONFIGS}
    print(f"{'id':5}{'type':12}" + "".join(f"{m:>15}" for m in CONFIGS))
    for q in queries:
        want = {tuple(e) for e in q["expected"]}
        row = []
        for m in CONFIGS:
            t0 = time.perf_counter()
            got = {(h["document"], h["section"]) for h in search(conn, q["query"], m, K, POOL)}
            latency[m].append((time.perf_counter() - t0) * 1000)
            r = len(want & got) / len(want)
            by_type[m][q["type"]].append(r)
            row.append(r)
        print(f"{q['id']:5}{q['type']:12}" + "".join(f"{r:15.2f}" for r in row))
    print("\nMean by type")
    print(f"{'type':17}" + "".join(f"{m:>15}" for m in CONFIGS))
    for t in TYPES:
        print(f"{t:17}" + "".join(f"{sum(by_type[m][t]) / len(by_type[m][t]):15.2f}" for m in CONFIGS))
    print(f"{'latency ms/query':17}" + "".join(f"{sum(latency[m]) / len(latency[m]):15.0f}" for m in CONFIGS))