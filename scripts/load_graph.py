import json
import os
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()
ROLES = {
    "acme_cloud_msa.pdf": "contract",
    "acme_sla_schedule.pdf": "contract",
    "northwind_vendor_security_policy.pdf": "policy",
    "fictional_data_protection_act_excerpt.pdf": "regulation",
    "acme_insurance_certificate.pdf": "certificate",
    "acme_invoice_0412.pdf": "invoice",
}
sections = [s for s in json.loads(Path("data/processed/sections.json").read_text())
            if not s["section"].startswith("0.")]
facts = json.loads(Path("data/processed/facts.json").read_text())

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", os.environ["NEO4J_PASSWORD"]))
with driver.session() as s:
    s.run("MATCH (n) DETACH DELETE n")
    s.run("CREATE CONSTRAINT doc_name IF NOT EXISTS FOR (d:Document) REQUIRE d.name IS UNIQUE")
    s.run("CREATE CONSTRAINT clause_id IF NOT EXISTS FOR (c:Clause) REQUIRE c.id IS UNIQUE")
    for name, role in ROLES.items():
        s.run("MERGE (d:Document {name: $n}) SET d.role = $r", n=name, r=role)
    for sec in sections:
        s.run("MATCH (d:Document {name: $doc}) "
              "MERGE (c:Clause {id: $id}) SET c.section = $sec, c.heading = $h, c.page = $p, c.text = $t "
              "MERGE (d)-[:HAS_CLAUSE]->(c)",
              doc=sec["document"], id=f"{sec['document']}#{sec['section']}", sec=sec["section"],
              h=sec["heading"], p=sec["page"], t=sec["text"])
    for f in facts:
        num = None if f["unit"] == "date" else float(f["value"])
        s.run("MATCH (c:Clause {id: $cid}) "
              "CREATE (c)-[:STATES]->(:Fact {attribute: $a, value: $v, num: $num, unit: $u, bound: $b, severity: $sev})",
              cid=f"{f['document']}#{f['section']}", a=f["attribute"], v=f["value"], num=num,
              u=f["unit"], b=f["bound"], sev=f["severity"])
    counts = s.run("MATCH (n) RETURN labels(n)[0] AS label, count(*) AS n ORDER BY label").data()
print(counts)