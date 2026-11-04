"""graph.py: citation graph over the documents in the library.

Edges are built when document A's reference list (parsed from its own
PDF text) matches the title of another document B in the library.
Titles are normalized (lowercase, punctuation stripped) before matching.

The collection itself only stores per-chunk metadata, so each document
is re-parsed on demand to recover its reference titles.
"""
from __future__ import annotations

import re
from typing import Optional

from app.indexer import VectorIndex
from app.parser import PdfParser

_NORM_RE = re.compile(r"[^a-z0-9]+")


def _norm_title(t: str) -> str:
    return _NORM_RE.sub(" ", t.lower()).strip()


def build_graph(idx: VectorIndex) -> dict:
    res = idx.collection.get(include=["metadatas"])
    docs: dict[str, dict] = {}
    for meta in res["metadatas"]:
        did = meta["doc_id"]
        if did not in docs:
            docs[did] = {
                "id": did,
                "title": meta["title"],
                "source": meta["source"],
                "chunks": 0,
            }
        docs[did]["chunks"] += 1

    # recover each document's reference titles by re-parsing its source
    refs_of: dict[str, list[str]] = {}
    for did, info in docs.items():
        try:
            doc = PdfParser().parse(info["source"])
            refs_of[did] = [_norm_title(r) for r in doc.references]
        except Exception:
            refs_of[did] = []

    # title index of library docs (skip generic OCR titles)
    title_index: dict[str, str] = {}
    for did, info in docs.items():
        if info["title"].startswith("Page "):
            continue
        title_index[_norm_title(info["title"])] = did

    edges: list[dict] = []
    for did, refs in refs_of.items():
        for rt in refs:
            if rt in title_index and title_index[rt] != did:
                edges.append({"source": did, "target": title_index[rt]})

    return {
        "nodes": [
            {"id": d["id"], "title": d["title"], "chunks": d["chunks"]}
            for d in docs.values()
        ],
        "edges": edges,
    }
