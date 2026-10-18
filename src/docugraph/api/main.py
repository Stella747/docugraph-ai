import hashlib
import json
import os
import sqlite3
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

DATA = Path(os.getenv("DOCUGRAPH_DATA", "data/processed"))
DB = DATA / "reviews.db"
REPORT = DATA / "report.json"
ROLES = DATA / "roles.json"
PAGE = Path(__file__).parent / "static" / "index.html"

app = FastAPI(title="DocuGraph AI")


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB)
    conn.execute("CREATE TABLE IF NOT EXISTS reviews (finding_id TEXT, decision TEXT, note TEXT, "
                 "edited_text TEXT, ts TEXT DEFAULT CURRENT_TIMESTAMP)")
    return conn


def _fid(item: dict) -> str:
    key = json.dumps([item["rule"], item["attribute"],
                      sorted((e["document"], e["section"]) for e in item["evidence"])])
    return hashlib.sha1(key.encode()).hexdigest()[:10]


def _items() -> list[dict]:
    if not REPORT.exists():
        raise HTTPException(503, "report.json not found; run scripts/run_report.py first")
    return [{**i, "id": _fid(i)} for i in json.loads(REPORT.read_text())]


class Review(BaseModel):
    finding_id: str
    decision: Literal["accept", "reject", "edit"]
    note: str = ""
    edited_text: str = ""


class Question(BaseModel):
    question: str


@app.get("/")
def index():
    return FileResponse(PAGE)


@app.get("/api/report")
def report():
    items = _items()
    with _conn() as c:
        rows = c.execute("SELECT finding_id, decision, note, edited_text FROM reviews WHERE rowid IN "
                         "(SELECT MAX(rowid) FROM reviews GROUP BY finding_id)").fetchall()
    latest = {r[0]: {"decision": r[1], "note": r[2], "edited_text": r[3]} for r in rows}
    return [{**i, "review": latest.get(i["id"])} for i in items]


@app.post("/api/review")
def review(r: Review):
    if r.finding_id not in {i["id"] for i in _items()}:
        raise HTTPException(404, "unknown finding")
    with _conn() as c:
        c.execute("INSERT INTO reviews (finding_id, decision, note, edited_text) VALUES (?, ?, ?, ?)",
                  (r.finding_id, r.decision, r.note, r.edited_text))
    return {"ok": True}


@app.get("/api/graph")
def graph():
    roles = json.loads(ROLES.read_text()) if ROLES.exists() else {}
    nodes, edges = {}, []
    for i in _items():
        docs = list(dict.fromkeys(e["document"] for e in i["evidence"]))
        for d in docs:
            nodes[d] = {"data": {"id": d, "label": d.replace(".pdf", "").replace("_", " "),
                                 "role": roles.get(d, "other")}}
        for a, b in zip(docs, docs[1:]):
            edges.append({"data": {"source": a, "target": b, "attribute": i["attribute"],
                                   "severity": i["severity"], "fid": i["id"]}})
    return {"nodes": list(nodes.values()), "edges": edges}


@app.post("/api/ask")
def ask_endpoint(q: Question):  # sync def: FastAPI runs it in a worker thread
    try:
        from docugraph.agents.ask import ask
        from docugraph.db import connect
        with connect() as conn:
            return ask(conn, q.question)
    except Exception as e:
        raise HTTPException(503, f"ask is unavailable ({type(e).__name__}); is Postgres up and Ollama running?")