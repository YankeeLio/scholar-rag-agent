"""EmbeddingService: BGE-M3 embeddings (local CPU default).

Design:
- Local BGE-M3 via sentence-transformers; caches model under the
  project's data/ dir so the C-drive user cache is not bloated.
- Model loads lazily on first encode() call (FastAPI startup stays fast).
- Queries get the BGE retrieval instruction prefix (dense search).
"""
from __future__ import annotations

import os
from typing import Optional

from app.config import HF_HOME, BGE_MODEL_NAME, EMBEDDING_DEVICE

# BGE instruction prefixes (official)
_INSTRUCTION_EN = "Represent this sentence for searching relevant passages: "
_INSTRUCTION_ZH = "为这个句子生成表示以用于检索相关文章： "


class EmbeddingService:
    """Wraps BGE-M3. Falls back to CPU when no CUDA is available."""

    def __init__(self, model_name: str = BGE_MODEL_NAME,
                 device: Optional[str] = None) -> None:
        self.model_name = model_name
        self.device = device or EMBEDDING_DEVICE
        self._model = None

    # ------------------------------------------------------------------
    def _ensure_model(self):
        if self._model is None:
            os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
            os.environ.setdefault("HF_HOME", str(HF_HOME))
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name,
                                              device=self.device)
        return self._model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        model = self._ensure_model()
        vecs = model.encode(texts, normalize_embeddings=True,
                            show_progress_bar=False)
        return [v.tolist() for v in vecs]

    def embed_query(self, query: str, language: str = "auto") -> list[float]:
        model = self._ensure_model()
        if language == "auto":
            language = "zh" if any("\u4e00" <= ch <= "\u9fff" for ch in query) else "en"
        instr = _INSTRUCTION_ZH if language == "zh" else _INSTRUCTION_EN
        vec = model.encode([instr + query], normalize_embeddings=True,
                           show_progress_bar=False)
        return vec[0].tolist()
