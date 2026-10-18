# Corpus B predictions

**Status:** <keep one line, delete the other>
- Written BEFORE running the pipeline on corpus B.

**Author:** Renu Meena. **Pipeline version:** unchanged from tag `pipeline-v1` (corpus B was run from a separate folder using the original code).

## Predictions

### 1. Issue detection
- **Expected detections:** 4 of 6 planted issues.
- **Expected misses:**
  - **Priority 1 vs Critical stress case (ISS-B6).** The rule engine matches severity by exact word (`critical`, `high`, `medium`, `low`). The mismatch between "Priority 1" and "Critical" will not join without an alias mapping.
  - **Insurance expiry (ISS-B4).** Possible miss or extraction failure, because the small local model may omit entities in complex date phrasing.

### 2. False alarms on controls
- **Expected:** 0 of 3.
- **Reasoning:** The control clauses meet or beat the policy and use matching severity words ("High"). The rules compare directions using `min` and `max` bounds, so compliant values should not trigger findings.

### 3. First stage to break
- **Expected:** the extraction and bound-rule layer. Phrasings such as "a floor of" and "not to be exceeded by" will fall back to `exact`, which can stop the directional rules from running.

## Outcome (added after the run)

| Prediction | Result |
|---|---|
| 4 of 6 detected | Correct: 4 of 6 detected |
| Priority 1 vs Critical missed | Correct (ISS-B6 missed; the contract clause carried no severity word) |
| Insurance expiry (ISS-B4) missed | Wrong: it was detected |
| Not predicted | ISS-B3 (insurance shortfall) was missed; all three extracted amounts were correct |
| 0 of 3 false alarms | 0 of 3 observed; whether the controls were real tests depends on their extracted bounds (check pending) |
| Extraction and bound layer breaks first | Partly supported: ISS-B3's miss is probably a bound problem (not yet verified); extraction values were correct on every planted clause |