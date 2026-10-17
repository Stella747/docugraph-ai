import json
from pathlib import Path

truth = json.loads(Path("evaluation/ground_truth.json").read_text())
findings = json.loads(Path("data/processed/findings.json").read_text())


def clause_set(evidence):
    return {(e["document"], e["section"]) for e in evidence}


page_truth = {(e["document"], e["section"]): e["page"]
              for group in ("issues", "decoys") for i in truth[group] for e in i["evidence"]}

matched = {i["id"]: [] for i in truth["issues"]}
decoy_hits, unexpected = [], []
for f in findings:
    cs, hit = clause_set(f["evidence"]), False
    for i in truth["issues"]:
        if cs <= clause_set(i["evidence"]):
            matched[i["id"]].append(f)
            hit = True
    for d in truth["decoys"]:
        if cs <= clause_set(d["evidence"]):
            decoy_hits.append(f)
            hit = True
    if not hit:
        unexpected.append(f)

detected = 0
cite_ok = cite_n = 0
for i in truth["issues"]:
    want = clause_set(i["evidence"])
    got = set().union(*[clause_set(f["evidence"]) for f in matched[i["id"]]]) if matched[i["id"]] else set()
    ok = got == want
    detected += ok
    print(f"{i['id']}  {'DETECTED' if ok else 'MISSED  '}  findings={len(matched[i['id']])}  evidence covered {len(got & want)}/{len(want)}")
    for f in matched[i["id"]]:
        for e in f["evidence"]:
            cite_n += 1
            cite_ok += page_truth.get((e["document"], e["section"])) == e["page"]

print(f"\nplanted issues detected: {detected}/{len(truth['issues'])}")
print(f"citation pages correct: {cite_ok}/{cite_n}")
print(f"decoy false alarms: {len(decoy_hits)}")
print(f"findings not in the answer key: {len(unexpected)}")
for f in unexpected:
    print("  UNKEYED:", f["rule"], f["attribute"], [(e["document"], e["section"], e["value"]) for e in f["evidence"]])