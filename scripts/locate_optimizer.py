"""Check where 'Adam optimizer / beta1 beta2' text lives in the v7 chunks."""
import json
import sys

sys.path.insert(0, r"G:\竞赛\2026传智杯-豆包\apps\api")
from app.indexer import VectorIndex  # noqa: E402

idx = VectorIndex()
res = idx.collection.get(include=["documents", "metadatas"])
out = []
for doc, meta in zip(res["documents"], res["metadatas"]):
    low = doc.lower()
    tags = []
    if "adam optimizer" in low:
        tags.append("ADAM")
    if "β1 = 0.9" in doc or "beta1" in low:
        tags.append("BETA1")
    if "warmup" in low:
        tags.append("warmup")
    if tags:
        out.append({
            "chunk_id": meta["chunk_id"],
            "section": meta["section"],
            "tags": tags,
            "head": doc[:160].replace("\n", " "),
        })
print(json.dumps(out, ensure_ascii=False, indent=2))
