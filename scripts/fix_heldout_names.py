import json
import shutil
from pathlib import Path

p = Path("evaluation/extraction_heldout.json")
shutil.copy(p, p.with_name("extraction_heldout.bak.json"))
items = json.loads(p.read_text())

RENAME = {
    "data_breach_notification_hours": ("breach_notice_hours", None),
    "cyber_insurance_limit_usd": ("cyber_insurance_usd", None),
    "critical_incident_response_hours": ("incident_response_hours", "critical"),
    "high_incident_response_hours": ("incident_response_hours", "high"),
}
for it in items:
    for f in it["facts"]:
        if f["attribute"] in RENAME:
            new_attr, sev = RENAME[f["attribute"]]
            f["attribute"] = new_attr
            if sev:
                f["severity"] = sev

p.write_text(json.dumps(items, indent=2))
print("rewrote", p)