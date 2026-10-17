import sqlite3

c = sqlite3.connect("data/processed/reviews.db")
rows = c.execute("SELECT decision, COUNT(*) FROM reviews WHERE rowid IN "
                 "(SELECT MAX(rowid) FROM reviews GROUP BY finding_id) GROUP BY decision").fetchall()
counts = dict(rows)
print(counts, f"reviewed {sum(counts.values())}/9")