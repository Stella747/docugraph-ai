import json
import re

MODEL = "qwen2.5:3b"
ATTRS = {  # attribute: (unit, description shown to the model)
    "incident_response_hours": ("hours", "time allowed to respond to an incident"),
    "breach_notice_hours": ("hours", "time allowed to notify of a personal data breach"),
    "payment_terms_days": ("days", "days allowed to pay an invoice"),
    "cyber_insurance_usd": ("usd", "cyber liability insurance amount in USD"),
    "contract_end_date": ("date", "date the agreement or its term ends"),
    "insurance_end_date": ("date", "date an insurance policy or coverage period ends"),
}
SCHEMA = {
    "type": "object",
    "properties": {"facts": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "attribute": {"type": "string", "enum": list(ATTRS)},
            "value": {"type": "string", "maxLength": 12},
        },
        "required": ["attribute", "value"],
    }}},
    "required": ["facts"],
}
SYSTEM = (
    "You extract contractual facts from one clause as JSON. Allowed attributes:\n"
    + "\n".join(f"- {k}: {d}" for k, (_, d) in ATTRS.items())
    + "\nExtract a fact only if the clause states a value for one of these attributes. Numbers that belong "
    "to other terms are not facts; return an empty list if the clause has none. Write values as plain numbers "
    "without commas (USD 2,000,000 -> 2000000) and dates as YYYY-MM-DD."
)
EXAMPLES = [  # deliberately unlike the gold clauses
    ("Acknowledgement: Provider must acknowledge urgent incidents within 3 hours of notification.",
     {"facts": [{"attribute": "incident_response_hours", "value": "3"}]}),
    ("General Provisions: Headings are for convenience only and do not affect interpretation.",
     {"facts": []}),
]
MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"], 1)}
MIN_CUES = ["at least", "not less than", "no less than", "no fewer than", "not fewer than", "minimum"]
MAX_CUES = ["within", "no later than", "not later than", "up to", "at most", "not more than",
            "no more than", "not exceed", "maximum"]


def bound_from_text(text: str, unit: str) -> str:
    t = text.lower()
    if unit == "date":
        return "exact"
    if any(c in t for c in MIN_CUES):
        return "min"
    if any(c in t for c in MAX_CUES):
        return "max"
    return "exact"


def grounded(value: str, unit: str, text: str) -> bool:
    """Keep a fact only if its value literally appears in the clause."""
    t = text.lower().replace(",", "")
    if unit == "date":
        found = set(re.findall(r"\d{4}-\d{2}-\d{2}", t))
        for d, mon, y in re.findall(r"(\d{1,2})\s+([a-z]+)\s+(\d{4})", t):
            if mon in MONTHS:
                found.add(f"{y}-{MONTHS[mon]:02d}-{int(d):02d}")
        return value in found
    return value in re.findall(r"\d+", t)


def _messages(heading: str, text: str) -> list[dict]:
    msgs = [{"role": "system", "content": SYSTEM}]
    for q, a in EXAMPLES:
        msgs += [{"role": "user", "content": q}, {"role": "assistant", "content": json.dumps(a)}]
    return msgs + [{"role": "user", "content": f"{heading}: {text}"}]


def extract(client, heading: str, text: str):
    """Returns (kept_facts, dropped_facts). Bound comes from cue words, not from the model."""
    resp = client.chat(model=MODEL, format=SCHEMA, options={"temperature": 0, "num_predict": 300},
                       messages=_messages(heading, text))
    kept, dropped = [], []
    for f in json.loads(resp["message"]["content"])["facts"]:
        unit = ATTRS[f["attribute"]][0]
        if grounded(f["value"], unit, text):
            kept.append({"attribute": f["attribute"], "value": f["value"], "unit": unit,
                         "bound": bound_from_text(text, unit)})
        else:
            dropped.append((f["attribute"], f["value"]))
    return kept, dropped