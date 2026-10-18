# Evaluation results

All documents are synthetic. Every test set was written by one author (the project author), and sets are small, so one clause moves a score by roughly 8 to 17 points. "Dev" sets were used to choose designs; "held-out" sets were written afterwards and scored once. Numbers on dev sets are not evidence of generalisation.

## 1. Retrieval

Corpus: 6 synthetic documents (about 60 chunks) with planted contradictions; ground truth in `evaluation/ground_truth.json`. Metric: Recall@3 over expected clauses. Systems: vector (bge-small), BM25, hybrid (RRF fusion of vector and keyword) followed by a cross-encoder rerank.

### Dev set (9 queries)
| type | vector | bm25 | hybrid + rerank (pool 20) |
|---|---|---|---|
| paraphrase | 0.89 | 0.28 | 0.78 |
| exact token | 0.25 | 1.00 | 1.00 |
| table | 1.00 | 1.00 | 1.00 |
| multi-hop | 0.00 | 0.50 | 0.50 |

### Fusion pool sweep (dev set, paraphrase recall)
| configuration | pool 3 | pool 5 | pool 10 | pool 20 |
|---|---|---|---|---|
| RRF of vector and Postgres full-text | 0.78 | 0.50 | 0.50 | 0.39 |
| RRF of vector and BM25 | 0.78 | 0.61 | 0.50 | 0.50 |

Plain fusion lowered paraphrase recall as the candidate pool grew. BM25 in place of Postgres full-text did not fix it. The cross-encoder rerank removed the dependence on pool size (pool 10 and 20 gave identical scores). A pool of 3 with k=3 can only reorder each method's top 3, so it would not generalise to a larger corpus.

### Held-out set (12 queries, scored once, tag `retrieval-v1`)
| type | vector | bm25 | hybrid + rerank |
|---|---|---|---|
| paraphrase | 1.00 | 0.92 | 1.00 |
| exact token | 0.50 | 1.00 | 1.00 |
| table | 1.00 | 1.00 | 1.00 |
| multi-hop | 1.00 | 1.00 | 0.75 |
| latency (ms/query) | 37 | 0 | 299 |

Findings:
- Vector search failed on exact-token queries in both sets (0.25 dev, 0.50 held-out).
- Hybrid + rerank had no collapsed query type in either set, but on the held-out set it did not beat BM25 alone (about 0.96 vs 0.97 overall) and cost about 300 ms per query.
- BM25's paraphrase score differed sharply between sets (0.28 vs 0.92), most likely because of differences in query wording and not method quality.
- Hybrid + rerank lost on H12 (a multi-document comparison); the cause was not investigated.

### Graph expansion (retrieved clauses plus the other side of any rule-detected conflict)
Measured on the 21 queries above, after the expansion was designed with knowledge of H12's failure, so this is a mechanism check and not a clean test.

| type | n | retrieval | with expansion | avg clauses passed to the model |
|---|---|---|---|---|
| paraphrase | 7 | 0.90 | 1.00 | 4.0 |
| exact token | 8 | 1.00 | 1.00 | 4.1 |
| table | 3 | 1.00 | 1.00 | 3.0 |
| multi-hop | 3 | 0.67 | 1.00 | 4.3 |

Expansion reads the rule findings; it is not a live Neo4j traversal.

## 2. Extraction (local qwen2.5:3b through Ollama)

### Dev set (12 corpus clauses plus filler)
- Model alone: recall 0.92, precision 0.73. It invented dates on filler clauses and labelled a certificate's policy end date as a contract end date.
- A literal-value guard (keep a value only if it appears in the clause) raised precision to 0.92 with no recall loss.
- Bound (max/min) was correct on only 3 of 11 matched facts when asked of the model, so it was replaced by a cue-word rule. After that change and a prompt revision, dev recall was 1.00 and precision 1.00 (the one earlier "false positive" was a start date missing from the key). These dev numbers were obtained after designing the fixes on those same clauses and say nothing about generalisation.

### First held-out attempt (diagnostic, discarded as a score)
Six of the eight positive clauses were labelled with attribute names outside the schema, so the score was invalid. It exposed three real gaps that were then fixed: no severity or resolution-time attribute, a date-format gap in the guard (dates written as "June 30, 2027"), and the model mislabelling facts when no valid attribute existed.

### Held-out set v1 (12 clauses: 8 positive, 4 negative; 10 facts; scored once; tag `extraction-v1`)
- Recall 0.90 (9 of 10 facts). Precision 1.00 (9 of 9 extracted facts valid).
- 0 false facts on the 4 negative clauses (which contained distractor numbers such as fees and other periods).
- Bound correct on 7 of 9 matched facts. The two misses used phrasings outside the cue-word list ("not to be exceeded by", "a floor of"); the rule fell back to `exact`.
- One unexplained miss (X6): the model returned nothing for a clearly stated end date. The guard dropped nothing. A possible cause is the wording "terminates" versus the attribute description "ends"; this was not tested.
- Severity was excluded from the scoring. The gold labels were not