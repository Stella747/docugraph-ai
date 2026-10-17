import json
import sys
from pathlib import Path

sys.path.insert(0, "scripts")
from generate_corpus import DOCS, FILLER_COUNT, FILLER_TEXT, TABLES

parsed = {(s["document"], s["section"]): s["text"]
          for s in json.loads(Path("data/processed/sections.json").read_text())}

bad = total = 0
for fname, (_, secs) in DOCS.items():
    for num, heading, text in secs:
        if (fname, num) in TABLES:
            continue  # table clauses are Markdown, compared separately
        total += 1
        got = parsed.get((fname, num))
        if got != text:
            bad += 1
            print(f"{fname} {num}\n  expected {text!r}\n  parsed   {got!r}")
print(f"\nreal clauses matching the generator text exactly: {total - bad}/{total}")

for fname, n in FILLER_COUNT.items():
    mism = sum(parsed.get((fname, f"0.{i}")) != FILLER_TEXT for i in range(1, n + 1))
    print(f"{fname}: {mism}/{n} filler clauses differ from the source text")