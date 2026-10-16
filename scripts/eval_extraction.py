import json
import sys
import time
from pathlib import Path

import ollama

from docugraph.extract.extractor import extract

mode = sys.argv[1] if len(sys.argv) > 1 else "dev"


def load_dev():
    secs = {(s["document"], s["section"]): s for s in json.loads(Path("data/processed/sections.json").read_text())}
    items = [{"id": f"{g['document'][:22]} {g['section']}", "heading": secs[(g["document"], g["section"])]["heading"],
              "text": secs[(g["document"], g["section"])]["text"], "facts": g["facts"]}
             for g in json.loads(Path("evaluation/extraction_gold.json").read_text())]
    filler = next(s for s in secs.values() if s["section"].startswith("0."))
    items.append({"id": "boilerplate", "heading": filler["heading"], "text": filler["text"], "facts": []})
    return items


items = load_dev() if mode == "dev" else json.loads(Path("evaluation/extraction_heldout.json").read_text())
client = ollama.Client(timeout=90)
tp = fp = fn = bound_ok = bound_n = neg_n = neg_bad = 0
for it in items:
    t0 = time.perf_counter()
    try:
        kept, dropped = extract(client, it["heading"], it["text"])
    except Exception as e:
        print(f"ERROR {it['id']}: {type(e).__name__}")
        kept, dropped = [], []
    want = {(f["attribute"], f["value"]): f for f in it["facts"]}
    have = {(f["attribute"], f["value"]): f for f in kept}
    tp += len(want.keys() & have.keys())
    fp += len(have.keys() - want.keys())
    fn += len(want.keys() - have.keys())
    if not want:
        neg_n += 1
        neg_bad += bool(have)
    for k in want.keys() & have.keys():
        bound_n += 1
        if want[k]["bound"] == have[k]["bound"]:
            bound_ok += 1
        else:
            print(f"  BOUND    {it['id']}  {k[0]}: gold={want[k]['bound']} got={have[k]['bound']}")
    flag = "ok      " if want.keys() == have.keys() else "MISMATCH"
    print(f"{flag} {time.perf_counter() - t0:4.1f}s {it['id']:30} dropped={dropped}", flush=True)
    if flag == "MISMATCH":
        print(f"     expected {sorted(want)}\n     got      {sorted(have)}", flush=True)

print(f"\n[{mode}] clauses: {len(items)}   recall {tp / max(tp + fn, 1):.2f}   "
      f"precision {tp / max(tp + fp, 1):.2f}   (tp={tp} fp={fp} fn={fn})")
print(f"bound correct on matched facts: {bound_ok}/{bound_n}")
print(f"negative clauses with a false fact: {neg_bad}/{neg_n}")