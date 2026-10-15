from functools import lru_cache

from sentence_transformers import SentenceTransformer

MODEL = "BAAI/bge-small-en-v1.5"  # 384 dimensions, small enough for CPU
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    return SentenceTransformer(MODEL, device="cpu")


def embed_passages(texts: list[str]):
    return _model().encode(texts, normalize_embeddings=True, batch_size=16, show_progress_bar=False)


def embed_query(query: str):
    return _model().encode(QUERY_PREFIX + query, normalize_embeddings=True)