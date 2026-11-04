"""VectorIndex: Chroma-backed collection for RAG retrieval.

Chunks carry metadata (doc_id/source/title/section/pages/line anchors/
ref_ids/chunk_id) so retrieval results can be rendered as traceable
citations. Chroma metadata values must be str/int/float/bool — lists
are serialized to comma-joined strings.
"""
from __future__ import annotations

from typing import Optional

from app.chunker import Chunk
from app.config import RETRIEVAL_TOP_K, VECTOR_DIR
from app.embedding import EmbeddingService
from app.parser import Document


def _pages_str(pages: list[int]) -> str:
    return ",".join(str(p) for p in pages)


def _refs_str(ref_ids: list[int]) -> str:
    return ",".join(str(r) for r in ref_ids)


class VectorIndex:
    """Persistent Chroma collection of paper chunks."""

    def __init__(self, persist_dir=None, collection_name: str = "papers") -> None:
        import chromadb
        self.persist_dir = str(persist_dir or VECTOR_DIR)
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    # ------------------------------------------------------------------
    def count(self) -> int:
        return self.collection.count()

    def add_document(self, doc: Document, chunks: list[Chunk],
                     embedding: EmbeddingService,
                     vecs: Optional[list[list[float]]] = None) -> None:
        if not chunks:
            return
        ids = [c.chunk_id for c in chunks]
        texts = [c.text for c in chunks]
        metas = [{
            "chunk_id": c.chunk_id,
            "doc_id": c.doc_id,
            "source": doc.source,
            "title": doc.title,
            "section": c.section,
            "pages": _pages_str(c.pages),
            "start_line": c.start_line,
            "end_line": c.end_line,
            "ref_ids": _refs_str(c.ref_ids),
        } for c in chunks]
        if vecs is None:
            vecs = embedding.embed_documents(texts)
        self.collection.add(ids=ids, documents=texts,
                            metadatas=metas, embeddings=vecs)

    # ------------------------------------------------------------------
    def search(self, query: str, embedding: EmbeddingService,
               top_k: Optional[int] = None) -> list[dict]:
        """Return top-k chunks with traceable metadata."""
        top_k = top_k or RETRIEVAL_TOP_K
        q = embedding.embed_query(query)
        res = self.collection.query(
            query_embeddings=[q],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        hits: list[dict] = []
        for doc_text, meta, dist in zip(
                res["documents"][0], res["metadatas"][0], res["distances"][0]):
            hits.append({
                "chunk_id": meta.get("chunk_id", ""),
                "text": doc_text,
                "metadata": meta,
                "score": round(1.0 - float(dist), 4),  # cosine similarity
            })
        return hits
