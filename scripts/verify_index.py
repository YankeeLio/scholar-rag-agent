"""Day2: verify index pipeline: parse -> chunk -> embed -> search.

Three fine-grained queries against 1706.03762v1; checks that top hits
carry the answer plus traceable anchors. Writes docs/index_verify.json.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, r"G:\竞赛\2026传智杯-豆包\apps\api")
from app.chunker import Chunker  # noqa: E402
from app.embedding import EmbeddingService  # noqa: E402
from app.indexer import VectorIndex  # noqa: E402
from app.parser import PdfParser  # noqa: E402

PDF = r"G:\竞赛\2026传智杯-豆包\pdf\1706.03762v1.pdf"
INDEX_DIR = r"G:\竞赛\2026传智杯-豆包\data\chroma_test"

QUERIES = [
    {
        "q": "What are the beta1 and beta2 values used for Adam optimization?",
        "hint": ["0.9", "0.98"],
    },
    {
        "q": "How many GPUs and how many days were used to train the big transformer?",
        "hint": ["eight", "8", "3.5"],
    },
    {
        "q": "What BLEU score did the Transformer achieve on WMT 2014 English-to-German?",
        "hint": ["28.4"],
    },
]

t0 = time.time()
doc = PdfParser().parse(PDF)
chunks = Chunker().chunk(doc)
print(f"[stage] parse+chunk: {time.time()-t0:.1f}s chunks={len(chunks)}")

emb = EmbeddingService()
t0 = time.time()
idx = VectorIndex(persist_dir=INDEX_DIR)
idx.add_document(doc, chunks, emb)
print(f"[stage] embed+index: {time.time()-t0:.1f}s count={idx.count()}")

results = {"indexed_chunks": idx.count(), "queries": []}
for item in QUERIES:
    t0 = time.time()
    hits = idx.search(item["q"], emb, top_k=3)
    for h in hits:
        h["contains_hint"] = [hint in h["text"] for hint in item["hint"]]
    results["queries"].append({
        "query": item["q"],
        "hints": item["hint"],
        "top3": hits,
        "search_secs": round(time.time() - t0, 2),
    })

Path(r"G:\竞赛\2026传智杯-豆包\docs\index_verify.json").write_text(
    json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
print("[done] wrote docs/index_verify.json")
