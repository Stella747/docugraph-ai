import json
import os
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()


def ev(doc, clause, fact):
    return (f"{{document: {doc}.name, section: {clause}.section, page: {clause}.page, "
            f"value: {fact}.value, bound: {fact}.bound}}")


RULES = {
    "requirement_vs_commitment": f"""
        MATCH (rd:Document)-[:HAS_CLAUSE]->(rc:Clause)-[:STATES]->(req:Fact),
              (ad:Document)-[:HAS_CLAUSE]->(ac:Clause)-[:STATES]->(act:Fact)
        WHERE rd.role IN ['policy','regulation'] AND ad.role IN ['contract','certificate']
          AND req.attribute = act.attribute AND req.severity = act.severity
          AND req.num IS NOT NULL AND act.num IS NOT NULL
          AND ((req.bound = 'max' AND act.num > req.num) OR (req.bound = 'min' AND act.num < req.num))
        RETURN req.attribute AS attribute, [{ev('rd', 'rc', 'req')}, {ev('ad', 'ac', 'act')}] AS evidence""",
    "internal_inconsistency": f"""
        MATCH (d1:Document {{role: 'contract'}})-[:HAS_CLAUSE]->(c1:Clause)-[:STATES]->(f1:Fact),
              (d2:Document {{role: 'contract'}})-[:HAS_CLAUSE]->(c2:Clause)-[:STATES]->(f2:Fact)
        WHERE c1.id < c2.id AND f1.attribute = f2.attribute AND f1.severity = f2.severity
          AND f1.num IS NOT NULL AND f2.num IS NOT NULL AND f1.num <> f2.num
        RETURN f1.attribute AS attribute, [{ev('d1', 'c1', 'f1')}, {ev('d2', 'c2', 'f2')}] AS evidence""",
    "coverage_gap": f"""
        MATCH (id:Document)-[:HAS_CLAUSE]->(ic:Clause)-[:STATES]->(ins:Fact {{attribute: 'insurance_end_date'}}),
              (cd:Document)-[:HAS_CLAUSE]->(cc:Clause)-[:STATES]->(fin:Fact {{attribute: 'contract_end_date'}})
        WHERE ins.value < fin.value
        RETURN 'insurance_coverage_gap' AS attribute, [{ev('id', 'ic', 'ins')}, {ev('cd', 'cc', 'fin')}] AS evidence""",
    "invoice_vs_contract": f"""
        MATCH (vd:Document {{role: 'invoice'}})-[:HAS_CLAUSE]->(vc:Clause)-[:STATES]->(inv:Fact {{attribute: 'payment_terms_days'}}),
              (cd:Document {{role: 'contract'}})-[:HAS_CLAUSE]->(cc:Clause)-[:STATES]->(con:Fact {{attribute: 'payment_terms_days'}})
        WHERE inv.num <> con.num
        RETURN 'payment_terms_days' AS attribute, [{ev('vd', 'vc', 'inv')}, {ev('cd', 'cc', 'con')}] AS evidence""",
}

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", os.environ["NEO4J_PASSWORD"]))
findings = []
with driver.session() as s:
    for rule, query in RULES.items():
        for rec in s.run(query):
            findings.append({"rule": rule, "attribute": rec["attribute"], "evidence": rec["evidence"]})

Path("data/processed/findings.json").write_text(json.dumps(findings, indent=2))
for f in findings:
    parts = " vs ".join(f"{e['document'][:22]} s{e['section']} p{e['page']} ({e['value']})" for e in f["evidence"])
    print(f"{f['rule']:26} {f['attribute']:26} {parts}")
print(f"\n{len(findings)} findings -> data/processed/findings.json")