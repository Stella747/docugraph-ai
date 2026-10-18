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
- Severity was excluded from the scoring. The gold labels were not derivable from the clauses: for several clauses they were risk ratings (for example a breach-notice clause labelled critical), and for the two SLA clauses they encoded mappings ("Priority 1" means critical) that are not in the text. Severity in the pipeline now comes from literal severity words in the clause and a hand-written risk policy in the report step.

## 3. Conflict detection (deterministic Cypher rules over the extracted fact graph)

| corpus | planted issues detected | citation pages correct | false alarms on controls |
|---|---|---|---|
| A (the system was built on it) | 7/7 | 16/16 | not measurable (the decoy clause type had no extractable attribute) |
| B (second corpus; pipeline unchanged; run once) | 4/6 | 10/10 | 0/3 (the policy bounds were max with matching severity words, so the controls were real tests) |

Corpus A: the pipeline first detected the 6 keyed issues and surfaced a true violation the answer key had omitted (the SLA schedule's Critical response time versus the policy). The key was extended to ISS-007 after that observation, so the 7/7 reflects a key edited after observation.

Corpus B: documents written by the author with new company names, values and wording; predictions are in `docs/corpus_b_predictions.md` (its status line says whether they were written before or after the run). Misses:
- ISS-B6 ("Priority 1" in the contract versus "Critical" in the policy): severity is matched by literal word, so the two facts were never compared. It failed silently, with no warning.
- ISS-B3 (insurance shortfall): all three extracted amounts were correct, so the miss was in the rule stage. The policy clause's bound was extracted as `exact` (no cue word matched), and the rule only compares `min` or `max` requirements, so the pair was never evaluated.

Date phrasings such as "March 31, 2028" were handled. The grounding guard dropped one invented value (a payment term the clause did not state).

## 4. Report agent (LangGraph: explain, verify, retry, template fallback)
- 9 of 9 explanations passed the verification check on the first attempt (118 s total on CPU). The check only confirms that every number in an explanation appears in the cited clauses.
- The retry and fallback paths did not trigger in that run; they are covered by a unit test with a stubbed explainer.
- Manual review of all 9 explanations (one reviewer, who is also the author): **6 accepted, 3 rejected**. Numeric grounding is not the same as narrative correctness; the verification check does not detect inverted reasoning or false-positive rules. Details are in section 5.

## 5. Report Explanation Evaluation (Human Review)

### Methodology & Results
The report generation agent produces grounded textual explanations for detected compliance contradictions. While automated verification checks that all numbers cited in the explanation exist within the underlying evidence text, manual review was conducted to evaluate narrative correctness, tone, and directionality.

- **Automated Numerical Verification:** 9/9 (100%) verified on the first attempt without triggering retry loops or template fallbacks.
- **Human Quality Review:** **6 of 9 explanations accepted upon manual review** (6 accepted / 3 rejected across $n=9$ total findings).

### Breakdown of Review Decisions ($n = 9$ Findings)
- **Accepted (6/9):** Accurately identified compliance gaps, shortfalls, and statutory threshold breaches with clear, sound logical direction.
- **Rejected (3/9):** Rejected due to narrative flaws, inverted directional claims, or false-positive findings surfaced by downstream rules (e.g., flagging matching quarterly review requirements as a breach).

### Summary Metric
> **"6 of 9 explanations accepted upon manual review."**

## 6. Ask a question (10 questions: 6 answerable, 4 unanswerable; scored once)
- Answerable answered: 4/6. Unanswerable refused: 2/4.
- Expected clauses cited on answered answerable questions: 1.00 (citation coverage only; answer text correctness was not scored).
- The 2 incorrect answers to unanswerable questions came from a rule-based fallback that lists detected conflicts touching the retrieved clauses without judging relevance.
- Smoke tests after the final prompt: one question was refused although both needed clauses were in context; another produced a fluent answer that conflated two unrelated clauses and passed all automated checks.
- Conclusion: automated checks (format, numbers present in the sources) do not detect wrong cross-clause reasoning by the 3B model. Free-form answers are labelled AI-generated in the UI; the rule-based findings are the reliable output. About 14 s per question on CPU.

## 7. Known limitations
- Synthetic documents only; all components were tuned on corpus A; test sets are small (n = 9 to 12) and written by one author; held-out topics overlap with dev topics.
- Extraction uses a closed list of eight attributes, and the guard only verifies numerals and dates.
- Direction (max/min) comes from a fixed cue-word list that failed on unfamiliar phrasings. Severity words must match literally; synonyms such as "Priority 1" or "P1" are not mapped.
- When direction or severity cannot be determined, the pipeline skips a pair silently. A needs-review finding would be safer.
- A 3B local model is unreliable at cross-clause reasoning, and the automated checks cannot detect that.
- No clean control run isolates the effect of image preprocessing on Docling's table detection (one degraded scan returned 0 tables before cleanup and 1 after, which is an observation, not a measured effect).
- Generated filler clauses all share section number 0.1 (generator numbering issue, not fixed). The planted issues and every cited clause are unaffected, but filler text is not uniquely addressable. Retrieval numbers were measured with that corpus.
- Reviewer decisions are stored but not used to improve anything.