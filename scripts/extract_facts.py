import json
import time
from pathlib import Path

import ollama

from docugraph.extract.extractor import extract
from docugraph.extract.rules import severity_from_text, table_facts

sections = json.loads(Path("data/processed/sections.json").read_text())
real = [s for s in sections if not s["section"].startswith("0.")]  # skip filler boilerplate
client = ollama.Client(timeout=240)
out = []
for s in real:
    t0 = time.perf_counter()
    if "|" in s["text"]:
        facts, dropped = table_facts(s["text"]), []
    else:
        kept, dropped = extract(client, s["heading"], s["text"])
        sev = severity_from_text(s["text"])
        facts = [{**f, "severity": sev} for f in kept]
    for f in facts:
        out.append({"document": s["document"], "section": s["section"], "page": s["page"],
                    "heading": s["heading"], **f})
    print(f"{time.perf_counter() - t0:4.1f}s {s['document'][:26]:26} {s['section']:5} "
          f"facts={[(f['attribute'], f['value'], f['severity']) for f in facts]} dropped={dropped}", flush=True)

Path("data/processed/facts.json").write_text(json.dumps(out, indent=2))
print(f"\n{len(out)} facts from {len(real)} clauses -> data/processed/facts.json")