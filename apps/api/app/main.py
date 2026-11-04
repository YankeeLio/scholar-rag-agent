"""FastAPI entrypoint for the full-flow research assistant Agent.

Day-2 skeleton: health / document upload (parse->chunk->index) /
document listing & detail / semantic search. The RAG QA endpoint
returns retrieved evidence and defers LLM generation until a
DeepSeek key is configured (Day 3).

Run:  cd apps/api && .venv\\Scripts\\uvicorn app.main:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app import config
from app.chunker import Chunker
from app.embedding import EmbeddingService
from app.indexer import VectorIndex
from app.parser import PdfParser

# ----------------------------------------------------------------------
# shared singletons
emb = EmbeddingService()
idx = VectorIndex()
_model_ready = threading.Event()
_model_error: dict | None = None

UPLOAD_DIR = config.DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _preload_model() -> None:
    """Load BGE-M3 in a background thread (fast startup)."""
    global _model_error
    try:
        emb._ensure_model()
    except Exception as exc:  # pragma: no cover - depends on runtime env
        _model_error = {"type": type(exc).__name__, "message": str(exc)}
    finally:
        _model_ready.set()


def _wait_model() -> None:
    _model_ready.wait(timeout=600)
    if _model_error:
        raise HTTPException(503, f"embedding model failed to load: {_model_error}")


@asynccontextmanager
async def lifespan(_: FastAPI):
    threading.Thread(target=_preload_model, daemon=True).start()
    yield


app = FastAPI(
    title="全流程科研助手 Agent API",
    description="PDF 解析 / RAG 检索 / 引用图谱 / 写作 Copilot 后端",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------------------------------------------------
# health
@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "model_loaded": _model_ready.is_set() and not _model_error,
        "model_error": _model_error,
        "index_count": idx.count(),
        "llm_configured": bool(config.LLM_API_KEY),
    }


# ----------------------------------------------------------------------
# upload: parse -> chunk -> embed -> index
@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)) -> dict:
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(400, "only PDF files are supported")
    dest = UPLOAD_DIR / file.filename
    dest.write_bytes(await file.read())

    _wait_model()
    doc = PdfParser().parse(dest)
    chunks = Chunker().chunk(doc)
    idx.add_document(doc, chunks, emb)

    return {
        "doc_id": Chunker._doc_id(str(dest)),
        "title": doc.title,
        "pages": doc.pages,
        "authors": doc.authors,
        "abstract": doc.abstract[:500],
        "section_titles": [s.title for s in doc.sections],
        "reference_count": len(doc.references),
        "table_count": len(doc.tables),
        "chunk_count": len(chunks),
        "index_count": idx.count(),
    }


# ----------------------------------------------------------------------
# documents: aggregate from Chroma metadata
@app.get("/api/documents")
def list_documents() -> dict:
    res = idx.collection.get(include=["metadatas"])
    docs: dict[str, dict] = {}
    for m in res["metadatas"]:
        did = m["doc_id"]
        entry = docs.setdefault(did, {
            "doc_id": did, "title": m["title"],
            "source": m["source"], "chunks": 0,
        })
        entry["chunks"] += 1
    return {"documents": sorted(docs.values(), key=lambda d: d["title"])}


# ----------------------------------------------------------------------
# document detail: re-parse the stored PDF
@app.get("/api/documents/{doc_id}")
def document_detail(doc_id: str) -> dict:
    res = idx.collection.get(where={"doc_id": doc_id}, include=["metadatas"])
    if not res["metadatas"]:
        raise HTTPException(404, "document not found in index")
    source = res["metadatas"][0]["source"]
    if not Path(source).exists():
        raise HTTPException(404, f"source pdf missing: {source}")
    doc = PdfParser().parse(source)
    return {
        "doc_id": doc_id,
        "title": doc.title,
        "authors": doc.authors,
        "abstract": doc.abstract,
        "pages": doc.pages,
        "sections": [s.__dict__ for s in doc.sections],
        "references": [r.__dict__ for r in doc.references],
        "tables": [t.__dict__ for t in doc.tables],
    }


# ----------------------------------------------------------------------
# semantic search
class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


@app.post("/api/search")
def search(req: SearchRequest) -> dict:
    _wait_model()
    hits = idx.search(req.query, emb, top_k=req.top_k)
    return {"query": req.query, "hits": hits}


# ----------------------------------------------------------------------
# RAG QA: evidence-first; LLM answer wired in on Day 3
class QARequest(BaseModel):
    question: str
    top_k: int = 5


@app.post("/api/qa")
def qa(req: QARequest) -> dict:
    _wait_model()
    hits = idx.search(req.question, emb, top_k=req.top_k)
    if not config.LLM_API_KEY:
        return {
            "answer": None,
            "note": "DEEPSEEK_API_KEY 未配置：已返回检索证据，配置后启用 LLM 生成回答",
            "citations": hits,
        }
    raise HTTPException(501, "LLM generation not wired yet (Day 3)")
