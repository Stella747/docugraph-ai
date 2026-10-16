# Retrieval evaluation

Corpus: 6 synthetic documents (~60 chunks) with planted contradictions; ground truth in `evaluation/ground_truth.json`.
Metric: Recall@3 over expected clauses. Systems: vector (bge-small), BM25, hybrid RRF + cross-encoder rerank.

## Dev set (9 queries; used to choose the design)
| type | vector | bm25 | hybrid_rerank (pool 20) |
|---|---|---|---|
| paraphrase | 0.89 | 0.28 | 0.78 |
| exact | 0.25 | 1.00 | 1.00 |
| table | 1.00 | 1.00 | 1.00 |
| multihop | 0.00 | 0.50 | 0.50 |

## Held-out set (12 queries, scored once, tag `retrieval-v1`)
| type | vector | bm25 | hybrid_rerank |
|---|---|---|---|
| paraphrase | 1.00 | 0.92 | 1.00 |
| exact | 0.50 | 1.00 | 1.00 |
| table | 1.00 | 1.00 | 1.00 |
| multihop | 1.00 | 1.00 | 0.75 |
| latency (ms/query) | 37 | 0 | 299 |

## Findings
- Vector search failed on exact-token queries in both sets (0.25 dev, 0.50 held-out).
- Hybrid + rerank had no collapsed query type in either set, but did not beat BM25 alone on held-out (about 0.96 vs 0.97 overall) and cost ~300 ms/query.
- BM25's paraphrase score differed sharply between sets (0.28 vs 0.92); likely a difference in query wording, not method quality.
- Hybrid + rerank lost on H12 (multi-document comparison); cause not yet established.
- Earlier negative results kept: Postgres full-text and BM25 fused with RRF underperformed on paraphrases at large candidate pools; the reranker removed the dependence on pool size.

## Limitations
n=12 held-out (one clause is about 8% of a type's score); small synthetic corpus; held-out topics overlap with dev topics; one author wrote all queries.