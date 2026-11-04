"""retriever.py: hybrid retrieval — dense (BGE-M3 cosine) + sparse (BM25).

Why hybrid: academic QA mixes fine-grained numeric questions ("what is
β1?") where lexical terms matter (sparse), and paraphrased conceptual
questions where semantics matter (dense). A weighted fusion covers both.

Scoring: final = w_dense * dense_sim + w_sparse * (BM25 score normalized
to [0,1] via min-max over the candidate set).
"""
from __future__ import annotations

import re
from typing import Optional

from app.config import RETRIEVAL_TOP_K
from app.embedding import EmbeddingService
from app.indexer import VectorIndex

DENSE_WEIGHT = 0.6
SPARSE_WEIGHT = 0.4

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    """Tokenize for BM25: English words + Chinese character bi-grams."""
    text = text.lower()
    tokens = _TOKEN_RE.findall(text)
    # keep Chinese chars as bi-grams so CJK queries can match
    cjk = re.findall(r"[\u4e00-\u9fff]", text)
    if len(cjk) >= 2:
        tokens.extend(cjk[i] + cjk[i + 1] for i in range(len(cjk) - 1))
    return tokens


class HybridRetriever:
    """Dense + sparse fusion over the persistent Chroma collection."""

    def __init__(self, idx: VectorIndex, embedding: EmbeddingService,
                 top_k: Optional[int] = None) -> None:
        self.idx = idx
        self.emb = embedding
        self.top_k = top_k or RETRIEVAL_TOP_K
        self._bm25 = None  # built lazily on first search

    # ------------------------------------------------------------------
    def _ensure_bm25(self):
        if self._bm25 is None:
            from rank_bm25 import BM25Okapi
            res = self.idx.collection.get(include=["documents", "metadatas"])
            corpus = [_tokenize(d) for d in res["documents"]]
            self._bm25 = BM25Okapi(corpus)
            self._bm25_ids = [m["chunk_id"] for m in res["metadatas"]]
        return self._bm25

    # ------------------------------------------------------------------
    def search(self, query: str, top_k: Optional[int] = None) -> list[dict]:
        top_k = top_k or self.top_k
        dense_hits = self.idx.search(query, self.emb, top_k=max(top_k * 3, 10))

        # sparse side
        bm25 = self._ensure_bm25()
        scores = bm25.get_scores(_tokenize(query))
        id2sparse = {cid: float(s) for cid, s in zip(self._bm25_ids, scores)}
        if id2sparse and max(id2sparse.values()) > 0:
            mx = max(id2sparse.values())
            mn = min(v for v in id2sparse.values() if v > 0)
            span = (mx - mn) or 1.0
            id2sparse = {k: (v - mn) / span for k, v in id2sparse.items()}
        else:
            id2sparse = {k: 0.0 for k in id2sparse}

        # fuse
        merged: dict[str, dict] = {}
        for h in dense_hits:
            cid = h["chunk_id"]
            merged[cid] = {
                "chunk_id": cid,
                "text": h["text"],
                "metadata": h["metadata"],
                "score": DENSE_WEIGHT * h["score"]
                         + SPARSE_WEIGHT * id2sparse.get(cid, 0.0),
                "dense": h["score"],
                "sparse": round(id2sparse.get(cid, 0.0), 4),
            }
        # candidates found only by sparse (rare) get dense=0
        for cid, s in id2sparse.items():
            if cid not in merged:
                # fetch its text/meta via collection
                got = self.idx.collection.get(ids=[cid],
                                              include=["documents", "metadatas"])
                if got["documents"]:
                    merged[cid] = {
                        "chunk_id": cid,
                        "text": got["documents"][0],
                        "metadata": got["metadatas"][0],
                        "score": SPARSE_WEIGHT * s,
                        "dense": 0.0,
                        "sparse": s,
                    }
        ranked = sorted(merged.values(), key=lambda x: -x["score"])
        return ranked[:top_k]
