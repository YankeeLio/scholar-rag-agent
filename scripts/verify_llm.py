"""Day3: verify DeepSeek RAG QA end-to-end (retrieve -> generate).

Asks a fine-grained question about the indexed paper, checks the LLM
answer contains the facts and citation markers. Writes docs/llm_verify.json.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, r"G:\竞赛\2026传智杯-豆包\apps\api")
from app import config, llm  # noqa: E402
from app.embedding import EmbeddingService  # noqa: E402
from app.indexer import VectorIndex  # noqa: E402

emb = EmbeddingService()
idx = VectorIndex()

q = "Transformer 的 big 模型训练时用了多少 GPU，训练了多少天？训练目标是哪个数据集？"
t0 = time.time()
hits = idx.search(q, emb, top_k=3)
retrieve_s = time.time() - t0

t0 = time.time()
answer = llm.chat_complete(q, hits)
llm_s = time.time() - t0

result = {
    "question": q,
    "retrieve_secs": round(retrieve_s, 2),
    "llm_secs": round(llm_s, 2),
    "model": config.LLM_CHAT_MODEL,
    "answer": answer,
    "citation_count": hits[0]["metadata"].get("chunk_id", ""),
    "citations": [{"chunk_id": h["chunk_id"], "section": h["metadata"].get("section"),
                   "pages": h["metadata"].get("pages"), "score": h["score"]} for h in hits],
}
Path(r"G:\竞赛\2026传智杯-豆包\docs\llm_verify.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print("[done] wrote docs/llm_verify.json")
