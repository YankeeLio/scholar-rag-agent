"""Inspect the Chroma sqlite to see what survived the corruption."""
import json
import sqlite3

db = r"G:\竞赛\2026传智杯-豆包\data\chroma\chroma.sqlite3"
con = sqlite3.connect(db)
cur = con.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]

out = {"tables": tables}
for t in tables:
    try:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        out[f"{t}_rows"] = cur.fetchone()[0]
    except Exception as e:
        out[f"{t}_err"] = str(e)

# embeddings table schema + sample
cur.execute("SELECT sql FROM sqlite_master WHERE name='embeddings'")
row0 = cur.fetchone()
out["embeddings_sql"] = row0[0] if row0 else None
cur.execute("SELECT COUNT(*) FROM embeddings")
out["embeddings_rows"] = cur.fetchone()[0]
cur.execute("SELECT * FROM embeddings LIMIT 1")
row = cur.fetchone()
if row:
    out["embedding_sample"] = {"cols": len(row), "col0": row[0], "col1_len": len(row[1]) if row[1] else 0}
con.close()
print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
