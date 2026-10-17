import json
import re
from pathlib import Path
from typing import TypedDict

import ollama
from langgraph.graph import END, StateGraph

MODEL = "qwen2.5:3b"
MAX_ATTEMPTS = 2
RISK_POLICY = {  # hand-written risk ratings; this is where severity is defined
    "incident_response_hours": "High",
    "breach_notice_hours": "High",
    "cyber_insurance_usd": "Medium",
    "insurance_coverage_gap": "Medium",
    "payment_terms_days": "Low",
}
SCHEMA = {
    "type": "object",
    "properties": {"explanation": {"type": "string"}, "recommended_action": {"type": "string"}},
    "required": ["explanation", "recommended_action"],
}
CLIENT = ollama.Client(timeout=240)
SECTIONS = {(s["document"], s["section"]): s
            for s in json.loads(Path("data/processed/sections.json").read_text())}


class State(TypedDict):
    findings: list[dict]
    index: int
    current: dict
    attempts: int
    draft: dict
    feedback: str
    reports: list[dict]


def _nums(text: str) -> set[str]:
    return set(re.findall(r"\d+", text.replace(",", "")))


def _evidence_text(finding: dict) -> str:
    parts = []
    for e in finding["evidence"]:
        parts.append(f"[{e['document']} section {e['section']}, page {e['page']}] "
                     f"{SECTIONS[(e['document'], e['section'])]['text']}")
    return "\n".join(parts)


def next_finding(state: State) -> dict:
    return {"current": state["findings"][state["index"]], "attempts": 0, "feedback": ""}


def explain(state: State) -> dict:
    f = state["current"]
    prompt = (
        "You are a compliance analyst. Explain the conflict below in 2 or 3 sentences and give one "
        "recommended action. Use ONLY the clauses provided. Do not introduce any number, date or "
        "document name that is not in the clauses.\n\n"
        f"Rule that flagged it: {f['rule']} ({f['attribute']})\n\nClauses:\n{_evidence_text(f)}\n"
        + (f"\nYour previous answer was rejected: {state['feedback']}\n" if state["feedback"] else "")
    )
    resp = CLIENT.chat(model=MODEL, format=SCHEMA, options={"temperature": 0, "num_predict": 400},
                       messages=[{"role": "user", "content": prompt}])
    return {"draft": json.loads(resp["message"]["content"]), "attempts": state["attempts"] + 1}


def verify(state: State) -> dict:
    f, d = state["current"], state["draft"]
    allowed = _nums(_evidence_text(f))
    for e in f["evidence"]:
        allowed |= set(re.findall(r"\d+", e["value"]))  # fact values, including date parts
    allowed |= _nums(f["attribute"])
    invented = _nums(d["explanation"] + " " + d["recommended_action"]) - allowed
    if invented:
        return {"feedback": f"these numbers do not appear in the clauses: {sorted(invented)}"}
    return {"feedback": ""}


def route_after_verify(state: State) -> str:
    if not state["feedback"]:
        return "accept"
    return "retry" if state["attempts"] < MAX_ATTEMPTS else "fallback"


def _record(state: State, explanation: str, action: str, verified: bool) -> dict:
    f = state["current"]
    return {"reports": state["reports"] + [{
        "rule": f["rule"], "attribute": f["attribute"],
        "severity": RISK_POLICY.get(f["attribute"], "Medium"),
        "explanation": explanation, "recommended_action": action,
        "verified": verified, "attempts": state["attempts"],
        "evidence": [{**e, "text": SECTIONS[(e["document"], e["section"])]["text"]} for e in f["evidence"]],
    }], "index": state["index"] + 1}


def accept(state: State) -> dict:
    d = state["draft"]
    return _record(state, d["explanation"], d["recommended_action"], True)


def fallback(state: State) -> dict:
    f = state["current"]
    vals = ", ".join(f"{e['document']} s{e['section']} says {e['value']}" for e in f["evidence"])
    return _record(state, f"Possible {f['attribute']} conflict: {vals}.",
                   "Review the cited clauses with the contract owner.", False)


def route_after_record(state: State) -> str:
    return "next" if state["index"] < len(state["findings"]) else "done"


def build():
    g = StateGraph(State)
    for name, fn in [("next_finding", next_finding), ("explain", explain), ("verify", verify),
                     ("accept", accept), ("fallback", fallback)]:
        g.add_node(name, fn)
    g.set_entry_point("next_finding")
    g.add_edge("next_finding", "explain")
    g.add_edge("explain", "verify")
    g.add_conditional_edges("verify", route_after_verify,
                            {"accept": "accept", "retry": "explain", "fallback": "fallback"})
    for node in ("accept", "fallback"):
        g.add_conditional_edges(node, route_after_record, {"next": "next_finding", "done": END})
    return g.compile()