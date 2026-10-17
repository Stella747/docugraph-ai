import json
from pathlib import Path

from docugraph.agents import report_graph as rg


def test_invented_number_triggers_retry_then_template_fallback(monkeypatch):
    calls = {"n": 0}

    def bad_explain(state):
        calls["n"] += 1
        return {"draft": {"explanation": "The vendor must respond within 999 hours.",
                          "recommended_action": "Escalate."},
                "attempts": state["attempts"] + 1}

    monkeypatch.setattr(rg, "explain", bad_explain)
    findings = json.loads(Path("data/processed/findings.json").read_text())[:1]
    final = rg.build().invoke(
        {"findings": findings, "index": 0, "reports": [], "feedback": "", "attempts": 0},
        {"recursion_limit": 50})
    report = final["reports"][0]
    assert calls["n"] == rg.MAX_ATTEMPTS   # retried, then gave up
    assert report["verified"] is False     # flagged as unverified
    assert "999" not in report["explanation"]  # the template text replaced the model's text