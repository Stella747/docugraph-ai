# Corpus B Pre-Run Predictions

## 1. Issue Detection Accuracy
* **Expected Detections:** 4 out of 6 planted issues detected.
* **Expected Misses:**
  * **Priority 1 vs. Critical SLA Stress Case:** Expected miss. The rule engine relies on exact literal string matching for severity levels (`critical`, `high`, `medium`, `low`). The cross-document terminology mismatch ("Priority 1" vs. "Critical") will fail to join without an explicit alias mapping layer.
  * **Insurance Expiry Date Miss:** Likely miss or extraction failure due to potential small-LLM entity extraction omissions on complex date/clause phrasing.

## 2. False Alarm Rate on Controls
* **Expected Control False Alarms:** 0 false positives across the 3 control pairs.
* **Reasoning:** The control clauses explicitly meet or exceed policy targets and use matching severity strings ("High"). The deterministic rule engine uses directed comparisons (`min`/`max` bounds), so compliant values will not trigger findings.

## 3. Anticipated Breakage Point
* **Primary Bottleneck:** The **Extraction / Bound Rule layer**. Held-out phrasing patterns ("a floor of", "not to be exceeded by") will trigger bound fallbacks to `exact`, which may prevent standard directional rules from executing cleanly on the extracted facts.

How many of the 6 planted issues will be detected?
How many false alarms on the 3 controls?
Which stage breaks first: extraction, the rules, or the answer key?