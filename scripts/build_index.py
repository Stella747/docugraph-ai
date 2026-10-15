import json
from pathlib import Path

from docugraph.db import connect
from docugraph.index.embedder import embed_passages

SCHEMA = """
CREATE EXTENSION IF NOT EXISTS vector;
DROP TABLE IF EXISTS chunks;
CREATE TABLE chunks (
    id SERIAL PRIMARY KEY,
    document TEXT, page INT, section TEXT, heading TEXT, text TEXT,
    embedding vector(384),
    tsv tsvector GENERATED ALWAYS AS (to_tsvector('english', heading || ' ' || text)) STORED
);
CREATE INDEX ON chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ON chunks USING gin (tsv);
"""


def context_text(r: dict) -> str:
    doc = Path(r["document"]).stem.replace("_", " ")
    return f"{doc} | section {r['section']} {r['heading']}: {r['text']}"


if __name__ == "__main__":
    rows = json.loads(Path("data/processed/sections.json").read_text())
    vectors = embed_passages([context_text(r) for r in rows])
    with connect() as conn:
        conn.execute(SCHEMA)
        for r, v in zip(rows, vectors):
            conn.execute(
                "INSERT INTO chunks (document, page, section, heading, text, embedding) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (r["document"], r["page"], r["section"], r["heading"], r["text"], v),
            )
    print(f"Indexed {len(rows)} chunks")