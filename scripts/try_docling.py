import sys
import time

from docling.document_converter import DocumentConverter

path = sys.argv[1]
start = time.time()
doc = DocumentConverter().convert(path).document
print(f"Converted in {time.time() - start:.1f}s, {len(doc.tables)} table(s) found\n")
print(doc.export_to_markdown())