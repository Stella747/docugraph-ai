import json
import re
from pathlib import Path

import ollama

from docugraph.retrieval.search import search

MODEL = "qwen2.5:3b"
CLIENT = ollama.Client(timeout=240)
NOT_FOUND = "NOT_FOUND"
MIN_WORDS = 8
SECTIONS = {(s["document"], s["section"]): s
            for s in json.loads(Path("data/processed/sections.json").read_text())}
FINDINGS = json.loads(Path("data/processed/findings.json").read_text())
SCHEMA = {
    "type": "object",
    "properties": {"answer": {"type": "string"},
                   "source_numbers": {"type": "array", "items": {"type": "integer"}}},
    "required": ["answer", "source_numbers"],
}


def expand(hit_keys: list[tuple]) -> tuple[list[tuple], list[dict]]:
    """Add the other side of every conflict that a retrieved clause takes part in."""
    ordered = list(dict.fromkeys(hit_keys))
    linked = []
    for f in FINDINGS:
        ev = [(e["document"], e["section"]) for e in f["evidence"]]
        if set(ev) & set(hit_keys):
            linked.append(f)
            ordered += [k for k in ev if k not in ordered]
    return ordered, linked


def _nums(text: str) -> set[str]:
    return set(re.findall(r"\d+", text.replace(",", "")))


def _cites(keys: list[tuple], numbers: list[int]) -> list[dict]:
    return [{"n": c, "document": keys[c - 1][0], "section": keys[c - 1][1],
             "page": SECTIONS[keys[c - 1]]["page"], "text": SECTIONS[keys[c - 1]]["text"]}
            for c in dict.fromkeys(numbers) if 1 <= c <= len(keys)]


def check(out: dict, n_sources: int, allowed: set[str]) -> tuple[bool, list[str]]:
    text = out["answer"].strip()
    answered = not text.upper().startswith(NOT_FOUND)
    problems = []
    if answered:
        if "[" in text or re.search(r"\bcited\b", text, re.I) or NOT_FOUND in text.upper():
            problems.append("the answer must be plain prose with no brackets, no 'cited' and no NOT_FOUND")
        if len(text.split()) < MIN_WORDS:
            problems.append(f"the answer must be a full sentence of at least {MIN_WORDS} words")
        if not out["source_numbers"]:
            problems.append("put the numbers of the sources you used in source_numbers")
        invented = _nums(text) - allowed
        if invented:
            problems.append(f"these numbers are not in the sources: {sorted(invented)}")
    elif out["source_numbers"]:
        problems.append(f"you listed sources but answered {NOT_FOUND}")
    if any(c < 1 or c > n_sources for c in out["source_numbers"]):
        problems.append(f"source numbers must be between 1 and {n_sources}")
    return answered, problems


def rule_answer(linked: list[dict], keys: list[tuple]) -> tuple[str, list[int]]:
    number = {k: i for i, k in enumerate(keys, 1)}
    parts, nums = [], []
    for f in linked:
        sides = [f"{e['document']} section {e['section']} states {e['value']}" for e in f["evidence"]]
        parts.append(f"{f['attribute']}: " + " versus ".join(sides))
        nums += [number[(e["document"], e["section"])] for e in f["evidence"]]
    return "Conflicts detected by rule involving the retrieved clauses: " + "; ".join(parts) + ".", nums


def ask(conn, question: str, expand_graph: bool = True, k: int = 3) -> dict:
    hits = search(conn, question, "hybrid_rerank", k)
    keys = [(h["document"], h["section"]) for h in hits]
    linked = []
    if expand_graph:
        keys, linked = expand(keys)
    number = {key: i for i, key in enumerate(keys, 1)}
    source_block = "\n".join(
        f"[{number[k]}] {k[0]}, section {k[1]}, page {SECTIONS[k]['page']}: {SECTIONS[k]['text']}" for k in keys)
    conflicts = "\n".join(
        f"- {f['attribute']}: sources " + " and ".join(
            f"[{number[(e['document'], e['section'])]}]" for e in f["evidence"]) + " disagree"
        for f in linked)
    allowed = _nums(source_block)
    for f in linked:
        for e in f["evidence"]:
            allowed |= set(re.findall(r"\d+", e["value"]))  # fact values, including date parts

    base = {"n_sources": len(keys), "expanded": expand_graph}
    feedback = ""
    for attempt in (1, 2):
        prompt = (
            "Answer the question in one or two plain sentences using ONLY the numbered sources. Write the "
            "sentences without brackets or source numbers; put the numbers of the sources you used in "
            f"source_numbers. Answer exactly {NOT_FOUND} with an empty source_numbers list only if none of "
            "the sources is relevant to the question. Do not introduce any number, date or name that is not "
            "in the sources.\n\n"
            f"Sources:\n{source_block}\n\n"
            + (f"Conflicts already detected by rule:\n{conflicts}\n\n" if conflicts else "")
            + f"Question: {question}\n"
            + (f"\nYour previous answer was rejected: {feedback}\n" if feedback else ""))
        resp = CLIENT.chat(model=MODEL, format=SCHEMA, options={"temperature": 0, "num_predict": 400},
                           messages=[{"role": "user", "content": prompt}])
        out = json.loads(resp["message"]["content"])
        answered, problems = check(out, len(keys), allowed)
        feedback = "; ".join(problems)
        if not problems:
            return {**base, "found": answered, "answer": out["answer"].strip() if answered else "",
                    "checks_passed": True, "attempts": attempt, "source": "model",
                    "citations": _cites(keys, out["source_numbers"]) if answered else []}
    if linked:  # the model failed twice: answer from the rule-detected conflicts instead
        text, nums = rule_answer(linked, keys)
        return {**base, "found": True, "answer": text, "checks_passed": True, "attempts": 2,
                "source": "rules", "citations": _cites(keys, nums)}
    return {**base, "found": False, "answer": "", "checks_passed": False, "attempts": 2,
            "source": "none", "citations": []}