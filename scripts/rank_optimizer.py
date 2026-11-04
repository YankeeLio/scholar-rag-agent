"""Check where the optimizer chunk ranks for the Chinese optimizer question."""
import json
import sys

sys.path.insert(0, r"G:\竞赛\2026传智杯-豆包\apps\api")
from app.embedding import EmbeddingService  # noqa: E402
from app.indexer import VectorIndex  # noqa: E402
from app.retriever import HybridRetriever  # noqa: E402

idx = VectorIndex()
emb = EmbeddingService()
r = HybridRetriever(idx, emb)

q = "用了什么优化器，β1 和 β2 是多少？"
hits = r.search(q, top_k=8)
out = {"query": q, "hits": []}
for i, h in enumerate(hits):
    out["hits"].append({
        "rank": i + 1,
        "chunk_id": h["chunk_id"],
        "section": h["metadata"]["section"],
        "score": round(h["score"], 4),
        "dense": round(h["dense"], 4),
        "sparse": h["sparse"],
        "has_adam": "adam optimizer" in h["text"].lower(),
        "head": h["text"][:100].replace("\n", " "),
    })
with open(r"G:\竞赛\2026传智杯-豆包\docs\hybrid_optimizer_rank.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("[done]")
