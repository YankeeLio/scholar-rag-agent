"""Verify hybrid retrieval (dense + BM25) on the v7 index."""
import json
import sys

sys.path.insert(0, r"G:\竞赛\2026传智杯-豆包\apps\api")
from app.embedding import EmbeddingService  # noqa: E402
from app.indexer import VectorIndex  # noqa: E402
from app.retriever import HybridRetriever  # noqa: E402

idx = VectorIndex()
emb = EmbeddingService()
r = HybridRetriever(idx, emb)

questions = [
    "Transformer 的 big 模型用了多少 GPU 训练，训练了几天？",
    "用了什么优化器，β1 和 β2 是多少？",
    "WMT 2014 英德任务上 big 模型的 BLEU 是多少？",
]
out = {"index_count": idx.count()}
for q in questions:
    hits = r.search(q, top_k=3)
    out[q] = [
        {
            "chunk_id": h["chunk_id"],
            "section": h["metadata"]["section"],
            "score": round(h["score"], 4),
            "dense": round(h["dense"], 4),
            "sparse": h["sparse"],
            "snippet": h["text"][:120].replace("\n", " "),
        }
        for h in hits
    ]

with open(r"G:\竞赛\2026传智杯-豆包\docs\hybrid_verify.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("[done] wrote docs/hybrid_verify.json")
