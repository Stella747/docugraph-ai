import sys

from docugraph.agents.ask import ask
from docugraph.db import connect

question = " ".join(a for a in sys.argv[1:] if a != "--no-expand")
with connect() as conn:
    r = ask(conn, question, expand_graph="--no-expand" not in sys.argv)

print(f"\nQ: {question}")
print(f"A: {r['answer'] if r['found'] else 'Not found in the documents.'}")
print(f"[checks_passed={r['checks_passed']} source={r['source']} attempts={r['attempts']} "
      f"sources_in_context={r['n_sources']} expanded={r['expanded']}]")
for c in r["citations"]:
    print(f"  [{c['n']}] {c['document']}, section {c['section']}, page {c['page']}: \"{c['text']}\"")