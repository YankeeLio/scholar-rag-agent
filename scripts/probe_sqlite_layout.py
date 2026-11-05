"""Probe Chroma sqlite schema (fixed)."""
import json
import sqlite3

db = r"G:\竞赛\2026传智杯-豆包\data\chroma\chroma.sqlite3"
con = sqlite3.connect(db)
cur = con.cursor()
out = {}

cur.execute("SELECT sql FROM sqlite_master WHERE name='embedding_metadata'")
out["embedding_metadata_sql"] = cur.fetchone()[0]

cur.execute("SELECT sql FROM sqlite_master WHERE name='embedding_fulltext_search_content'")
r = cur.fetchone()
out["fts_content_sql"] = r[0] if r else None

cur.execute("SELECT sql FROM sqlite_master WHERE name='embedding_fulltext_search_data'")
r = cur.fetchone()
out["fts_data_sql"] = r[0] if r else None

cur.execute("SELECT * FROM embedding_metadata LIMIT 3")
out["meta_sample"] = cur.fetchall()

con.close()
with open(r"G:\竞赛\2026传智杯-豆包\docs\debug_sqlite_layout.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("[done]")
