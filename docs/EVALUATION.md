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

# Evaluation Results: Extraction v1

## Held-Out Evaluation Summary
- **Dataset Size:** 12 clauses (8 positives, 4 negatives), yielding 10 ground-truth facts.
- **Recall:** 0.90 (9/10 facts extracted; 1 unexplained miss in X6).
- **Precision:** 1.00 (9/9 extracted facts valid).
- **Negative Rejection:** 100% (0 false positive facts extracted across 8 negative clauses).
- **Bound Rule Accuracy:** 7/9 (77.8%). Failed on held-out vocabulary phrasings ("not to be exceeded by", "a floor of"), falling back to `exact`.

---

## Detailed Findings & Diagnostic Analysis

### 1. Exclusion of Severity Scoring
- **Root Cause:** Severity gold labels were not derivable from clause text alone. 
  - For non-SLA clauses (X1, X2, X3, X5, X8), labels reflected post-extraction risk ratings (e.g., classifying a breach notice as "critical" or contract start as "low"), which are assigned downstream by the Risk Agent rather than stated in text.
  - For SLA clauses (X4, X7), labels encoded external mapping rules (e.g., mapping "Priority 1" to "critical" and "Major System Vulnerability" to "high") that were absent from the raw clause text.
- **Conclusion:** The severity metric is excluded from the evaluation result as invalid. 

### 2. Bound Rule Vocabulary Gaps
- **Root Cause:** The two bound rule misses (X1 and X2) were direct hits on held-out vocabulary phrases ("not to be exceeded by" for `max` and "a floor of" for `min`). 
- **Conclusion:** The deterministic cue-word rule functions as designed on familiar training vocabulary, but lacks generalization on unseen phrasing.

### 3. Unexplained Extraction Miss (X6)
- **Observation:** The model returned an empty list (`[]`) in 1.2 seconds on X6, which explicitly contains the date "December 31, 2028". The deterministic guard dropped nothing (`dropped=[]`), indicating the 3B model failed to generate the fact entity during its pass.
- **Hypothesis:** Potential mismatch between the prompt attribute description ("ends") and the clause wording ("terminates"), though unverified.

---

## Architecture Limitations & Technical Debt
- **Sample Size:** Evaluation set is small ($n = 12$ clauses, 10 facts); recall of 0.90 rests on a limited total count.
- **Single-Author Corpus:** Potential single-author bias in held-out test generation.
- **Deterministic Severity Alias Gap:** The current pipeline's severity rule relies on exact string matches (`critical`, `high`, `medium`, `low`). It lacks a per-document severity alias mapping layer to handle standard industry taxonomy (e.g., "Priority 1", "P1", "Sev 2").
- **Small-Model Capacity:** Performance bound by the extraction capabilities of a 3B parameter local LLM supplemented by hand-built rule layers.

* **Answer Key Note:** ISS-007 was added to the answer key after the pipeline surfaced a true violation the key had omitted; the 7/7 score therefore reflects a key edited after observation.

## Ask-a-question (10 questions: 6 answerable, 4 unanswerable; scored once)
- Answerable answered: 4/6. Unanswerable refused: 2/4.
- Expected clauses cited on answered answerable questions: 1.00 (citation coverage only; answer text correctness not scored).
- The 2 incorrect answers to unanswerable questions came from the rule-based fallback, which lists detected conflicts touching the retrieved clauses without judging relevance.
- Smoke tests after the final prompt: one question refused although both needed clauses were in context; one produced a fluent answer that conflated two unrelated clauses and passed all automated checks.
- Conclusion: automated checks (format, numbers present in sources) do not detect wrong cross-clause reasoning by the 3B model. Free-form answers are labelled AI-generated in the UI; rule-based findings are the reliable output.

## Known limitations
- Generated filler clauses all share section number 0.1 (generator numbering issue, not fixed). The planted issues and all cited clauses are unaffected, but filler text is not uniquely addressable.
- All components were tuned on one synthetic corpus; held-out sets are small (n=9 to 12) and written by one author.
- Severity labels come from a hand-written risk policy, not from the documents. Severity words in clauses are matched literally ("Critical"); synonyms such as "Priority 1" are not mapped.
- Bound detection (max/min) uses a fixed cue-word list that failed on unfamiliar phrasings in held-out clauses.
- Local 3B model on CPU; ~14 s per question.