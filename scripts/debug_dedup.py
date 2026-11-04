"""Debug dedup: inspect Chroma get(embeddings) and compute v1-vs-v7 similarity."""
import json
import sys

sys.path.insert(0, r"G:\竞赛\2026传智杯-豆包\apps\api")
from app.chunker import Chunker  # noqa: E402
from app.dedup import _cos, dedup_check  # noqa: E402
from app.embedding import EmbeddingService  # noqa: E402
from app.indexer import VectorIndex  # noqa: E402
from app.parser import PdfParser  # noqa: E402

idx = VectorIndex()
res = idx.collection.get(include=["embeddings", "metadatas"])
meta_count = len(res["metadatas"])
emb_ok = res["embeddings"] is not None
emb_count = len(res["embeddings"]) if emb_ok else 0

out = {
    "meta_count": meta_count,
    "embeddings_returned": emb_ok,
    "embeddings_count": emb_count,
    "first_meta": res["metadatas"][0] if meta_count else None,
    "first_emb_len": len(res["embeddings"][0]) if (emb_ok and emb_count) else None,
}

# v7 chunks
doc = PdfParser().parse(r"G:\竞赛\2026传智杯-豆包\data\uploads\1706.03762v7.pdf")
chunks = Chunker().chunk(doc)
emb = EmbeddingService()

warns = dedup_check(str(doc.source), doc.title, chunks, emb, idx)
out["dedup_warnings"] = warns

# manual: v1 vs v7 avg max-pairwise
new_vecs = emb.embed_documents([c.text for c in chunks])
existing = {}
for meta, vec in zip(res["metadatas"], res["embeddings"]):
    did = meta["doc_id"]
    existing.setdefault(did, []).append(vec)
manual = {}
for did, vecs in existing.items():
    sims = []
    for nv in new_vecs:
        sims.append(max(_cos(nv, ev) for ev in vecs))
    manual[did] = {"avg": round(sum(sims)/len(sims), 4), "min": round(min(sims), 4), "max": round(max(sims), 4)}
out["manual_sims"] = manual

with open(r"G:\竞赛\2026传智杯-豆包\docs\debug_dedup.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("[done] wrote docs/debug_dedup.json")
