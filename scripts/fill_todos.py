import re
import sys
from pathlib import Path

CONTROLS = "policy bounds were max with matching severity words, so the controls were real tests"
B3 = ("the policy clause's bound was extracted as exact because its wording matched no cue word, and the "
      "rule only compares min or max requirements, so the pair was never evaluated")
arg = sys.argv[1] if len(sys.argv) > 1 else None
REVIEW = None if arg is None else ("not yet performed" if arg == "skip" else arg)


def read(path):
    return Path(path).read_text(encoding="utf-8")


def write(path, text):
    Path(path).write_text(text, encoding="utf-8")


def fill(path, key, new):
    t = read(path)
    m = re.search(r"<FILL:[^>]*" + re.escape(key) + r"[^>]*>", t)
    if not m:
        print(f"NOT FOUND in {path}: <FILL ... {key} ...>")
        return
    write(path, t[:m.start()] + new + t[m.end():])
    print(f"ok {path}: {key}")


def sub(path, old, new):
    t = read(path)
    if old not in t:
        print(f"NOT FOUND in {path}: {old[:60]!r}")
        return
    write(path, t.replace(old, new, 1))
    print(f"ok {path}: {old[:50]!r}")


EV = "docs/EVALUATION.md"
fill(EV, "controls had", CONTROLS)
fill(EV, "confirmed cause", B3)
if REVIEW:
    fill(EV, "review_stats", REVIEW)

RD = "README.md"
sub(RD, "0/3 TODO: confirm the controls had max/min bounds |",
    "0/3 (controls had max bounds and matching severity words, so they were real tests) |")
sub(RD, 'an insurance shortfall TODO: state the confirmed cause from the bound check, or write "cause not confirmed".',
    "an insurance shortfall (the policy clause's bound was extracted as `exact`, so the rule that compares "
    "`min` or `max` requirements never evaluated the pair).")
if REVIEW:
    new = "not yet performed" if arg == "skip" else f"{REVIEW} (one reviewer, who is also the author)"
    sub(RD, "TODO accepted / edited / rejected counts from `scripts/review_stats.py` (one reviewer, who is also the author)", new)

PR = "docs/corpus_b_predictions.md"
sub(PR, "| 0 of 3 false alarms | 0 of 3 observed; whether the controls were real tests depends on their extracted bounds (check pending) |",
    "| 0 of 3 false alarms | 0 of 3 observed; the policy clauses had max bounds with matching severity words, so the controls were real tests |")
sub(PR, "| Extraction and bound layer breaks first | Partly supported: ISS-B3's miss is probably a bound problem (not yet verified); extraction values were correct on every planted clause |",
    "| Extraction and bound layer breaks first | Supported: ISS-B3 was missed because the policy clause's bound was extracted as exact; extraction values were correct on every planted clause |")