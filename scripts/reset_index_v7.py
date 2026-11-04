"""Reset the index: drop the v7 doc (85ca48a70a7d), keep only v1 (e2aef5484cbd).

Used to re-test the official dedup scenario (library holds v1, upload v7).
"""
import sys

sys.path.insert(0, r"G:\竞赛\2026传智杯-豆包\apps\api")
from app.indexer import VectorIndex  # noqa: E402

idx = VectorIndex()
dropped = idx.collection.delete(where={"doc_id": "85ca48a70a7d"})
count = idx.count()
print(f"dropped {dropped}, remaining count = {count}")
