"""FastAPI entrypoint for the full-flow research assistant Agent.

Day-2 skeleton: health / document upload (parse->chunk->index) /
document listing & detail / semantic search. The RAG QA endpoint
returns retrieved evidence and defers LLM generation until a
DeepSeek key is configured (Day 3).

Run:  cd apps/api && .venv\\Scripts\\uvicorn app.main:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import json as _json
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app import config, dedup, llm
from app.chunker import Chunker
from app.embedding import EmbeddingService
from app.indexer import VectorIndex
from app.parser import PdfParser
from app.retriever import HybridRetriever

# ----------------------------------------------------------------------
# shared singletons
emb = EmbeddingService()
idx = VectorIndex()
retriever = HybridRetriever(idx, emb)
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
# upload: parse -> chunk -> dedup check -> embed -> index
@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...),
                          replace: bool = False) -> dict:
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(400, "only PDF files are supported")
    dest = UPLOAD_DIR / file.filename
    dest.write_bytes(await file.read())

    _wait_model()
    doc = PdfParser().parse(dest)
    chunks = Chunker().chunk(doc)
    doc_id = Chunker._doc_id(str(dest))

    # content-based semantic dedup against the library (arXiv v1/v7 case)
    warnings = dedup.dedup_check(str(dest), doc.title, chunks, emb, idx)
    if warnings and not replace:
        return {
            "doc_id": doc_id,
            "title": doc.title,
            "pages": doc.pages,
            "dedup_warning": warnings,
            "indexed": False,
            "note": "检测到库中存在高相似论文，未入库。可携带 ?replace=true 强制替换，"
                    "或上传其他文件。",
        }

    if replace and warnings:
        # drop every chunk of the old near-duplicate document
        for w in warnings:
            idx.collection.delete(where={"doc_id": w["existing_doc_id"]})

    idx.add_document(doc, chunks, emb)
    return {
        "doc_id": doc_id,
        "title": doc.title,
        "pages": doc.pages,
        "authors": doc.authors,
        "abstract": doc.abstract[:500],
        "section_titles": [s.title for s in doc.sections],
        "reference_count": len(doc.references),
        "table_count": len(doc.tables),
        "chunk_count": len(chunks),
        "dedup_warning": warnings or None,
        "indexed": True,
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
    hits = retriever.search(req.query, top_k=req.top_k)
    return {"query": req.query, "hits": hits}


# ----------------------------------------------------------------------
# RAG QA: retrieve -> evidence -> DeepSeek generation (streaming)
class QARequest(BaseModel):
    question: str
    top_k: int = 5


def _run_qa(req: QARequest) -> tuple[list[dict], str | None]:
    """Shared retrieval; returns (hits, note_if_no_key)."""
    _wait_model()
    hits = retriever.search(req.question, top_k=req.top_k)
    if not config.LLM_API_KEY:
        return hits, "DEEPSEEK_API_KEY 未配置：已返回检索证据，配置后启用 LLM 生成回答"
    return hits, None


@app.post("/api/qa")
def qa(req: QARequest) -> dict:
    hits, note = _run_qa(req)
    if note:
        return {"answer": None, "note": note, "citations": hits}
    answer = llm.chat_complete(req.question, hits)
    return {"answer": answer, "citations": hits}


@app.post("/api/qa/stream")
def qa_stream(req: QARequest) -> StreamingResponse:
    hits, note = _run_qa(req)
    if note:
        raise HTTPException(400, note)

    def gen():
        # 1) evidence first so the UI can render citations immediately
        yield "data: " + _json.dumps(
            {"type": "citations", "citations": hits},
            ensure_ascii=False) + "\n\n"
        # 2) token stream
        for delta in llm.chat_stream(req.question, hits):
            yield "data: " + _json.dumps(
                {"type": "delta", "text": delta},
                ensure_ascii=False) + "\n\n"
        yield "data: " + _json.dumps(
            {"type": "done"}, ensure_ascii=False) + "\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


# ----------------------------------------------------------------------
# static frontend (served at /); mount last so API routes take priority
WEB_DIR = config.ROOT_DIR / "apps" / "web"
if WEB_DIR.exists():
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
