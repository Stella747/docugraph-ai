from docugraph.db import connect
from docugraph.retrieval.search import search

q = "How quickly must the supplier react when something breaks badly?"
with connect() as conn:
    for mode in ("vector", "keyword", "hybrid"):
        print(mode)
        for h in search(conn, q, mode, 5):
            print("  ", h["document"], h["section"], h["heading"])