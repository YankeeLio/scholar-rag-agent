"""dedup.py: content-based semantic deduplication (arXiv v1 vs v7 use case).

Approach: embed the new document's chunks, compare them against every
existing document's chunk embeddings (max-pairwise cosine, averaged).
If the average similarity exceeds a threshold, the documents are
flagged as near-duplicates; version hints are extracted from filenames
("1706.03762v7.pdf" -> v7) so the system can recommend keeping the
newest version.
"""
from __future__ import annotations

import re
from typing import Optional

from app.chunker import Chunk
from app.embedding import EmbeddingService
from app.indexer import VectorIndex

DEDUP_THRESHOLD = 0.85  # avg max-pairwise cosine above this -> duplicate
# (v1 vs v7 measured at 0.899; unrelated papers usually < 0.70)

_VERSION_RE = re.compile(r"v(\d+)\s*\.pdf$", re.IGNORECASE)


def _version_of(source: str) -> Optional[int]:
    name = source.replace("\\", "/").split("/")[-1]
    m = _VERSION_RE.search(name)
    return int(m.group(1)) if m else None


def dedup_check(new_source: str, new_title: str,
                new_chunks: list[Chunk], embedding: EmbeddingService,
                idx: VectorIndex) -> list[dict]:
    """Compare the new doc's chunks against existing docs in the index.

    Returns a list of warning dicts (empty when no near-duplicate found).
    """
    if not new_chunks:
        return []

    # all existing vectors grouped by doc_id
    res = idx.collection.get(include=["embeddings", "metadatas"])
    by_doc: dict[str, dict] = {}
    for meta, vec in zip(res["metadatas"], res["embeddings"]):
        did = meta["doc_id"]
        by_doc.setdefault(did, {"title": meta["title"], "source": meta["source"],
                                "vecs": []})["vecs"].append(vec)

    new_vecs = embedding.embed_documents([c.text for c in new_chunks])

    warnings: list[dict] = []
    for did, info in by_doc.items():
        sims = []
        for nv in new_vecs:
            best = max(_cos(nv, ev) for ev in info["vecs"])
            sims.append(best)
        avg = sum(sims) / len(sims)
        if avg >= DEDUP_THRESHOLD:
            warnings.append({
                "existing_doc_id": did,
                "existing_title": info["title"],
                "existing_source": info["source"],
                "avg_similarity": round(avg, 4),
                "threshold": DEDUP_THRESHOLD,
                "recommendation": _recommend(info["source"], new_source),
            })
    return warnings


def _recommend(existing_source: str, new_source: str) -> str:
    ev, nv = _version_of(existing_source), _version_of(new_source)
    if ev is not None and nv is not None:
        if nv > ev:
            return f"库中已有 v{ev}，本次上传 v{nv} 较新，建议用新版本替换"
        if nv < ev:
            return f"库中已有较新版本 v{ev}，本次上传 v{nv} 较旧，建议保留库中版本"
    return "库中已存在高度相似的论文，建议确认后决定保留或替换"


def _cos(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))
