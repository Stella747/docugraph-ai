import re

from docugraph.index.embedder import embed_query
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder

_bm25, _bm25_rows = None, None


COLS = "id, document, section, page, heading"


def _vector(conn, query: str, k: int):
    return conn.execute(
        f"SELECT {COLS} FROM chunks ORDER BY embedding <=> %s LIMIT %s",
        (embed_query(query), k),
    ).fetchall()


def _keyword(conn, query: str, k: int):
    words = re.findall(r"[A-Za-z0-9]+", query.lower())
    if not words:
        return []
    tsq = " | ".join(words)  # OR semantics: a natural question never matches every word
    return conn.execute(
        f"SELECT {COLS} FROM chunks WHERE tsv @@ to_tsquery('english', %s) "
        "ORDER BY ts_rank_cd(tsv, to_tsquery('english', %s)) DESC LIMIT %s",
        (tsq, tsq, k),
    ).fetchall()


def _rrf(rankings: list[list], k: int, c: int = 60):
    """Reciprocal Rank Fusion: a chunk scores 1/(c+rank) from each list it appears in."""
    scores, rows = {}, {}
    for ranking in rankings:
        for rank, row in enumerate(ranking):
            scores[row[0]] = scores.get(row[0], 0) + 1 / (c + rank + 1)
            rows[row[0]] = row
    best = sorted(scores, key=scores.get, reverse=True)[:k]
    return [rows[i] for i in best]

def _tok(s: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", s.lower())


def _bm25_search(conn, query: str, k: int):
    global _bm25, _bm25_rows
    if _bm25 is None:  # build the in-memory index once
        _bm25_rows = conn.execute(f"SELECT {COLS}, text FROM chunks ORDER BY id").fetchall()
        _bm25 = BM25Okapi([_tok(r[4] + " " + r[5]) for r in _bm25_rows])
    scores = _bm25.get_scores(_tok(query))
    top = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
    return [_bm25_rows[i][:5] for i in top if scores[i] > 0]

_ce = None


def _rerank(conn, query: str, rows: list, k: int):
    global _ce
    if _ce is None:
        _ce = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", device="cpu")
    ids = [r[0] for r in rows]
    texts = dict(conn.execute("SELECT id, text FROM chunks WHERE id = ANY(%s)", (ids,)).fetchall())
    scores = _ce.predict([(query, f"{r[4]}: {texts[r[0]]}") for r in rows])
    order = sorted(range(len(rows)), key=lambda i: scores[i], reverse=True)[:k]
    return [rows[i] for i in order]

def search(conn, query: str, mode: str = "hybrid", k: int = 5, pool: int = 20) -> list[dict]:
    if mode == "vector":
        hits = _vector(conn, query, k)
    elif mode == "keyword":
        hits = _keyword(conn, query, k)
    elif mode == "bm25":
        hits = _bm25_search(conn, query, k)
    elif mode == "hybrid_bm25":
        hits = _rrf([_vector(conn, query, pool), _bm25_search(conn, query, pool)], k)
    elif mode == "vector_rerank":
        hits = _rerank(conn, query, _vector(conn, query, pool), k)
    elif mode == "hybrid_rerank":
        fused = _rrf([_vector(conn, query, pool), _bm25_search(conn, query, pool)], pool)
        hits = _rerank(conn, query, fused, k)
    else:
        hits = _rrf([_vector(conn, query, pool), _keyword(conn, query, pool)], k)
    return [{"document": h[1], "section": h[2], "page": h[3], "heading": h[4]} for h in hits]