"""graph.py: citation graph over the documents in the library.

Robust matching strategy: an edge A -> B exists when B's normalized
title appears anywhere in A's full text (works for both arXiv-style
numbered references and APA-style bibliographies, e.g. the 541-page
Understanding Deep Learning textbook). Titles are normalized to
lowercase alphanumerics before matching.
"""
from __future__ import annotations

import re

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

    # full normalized text per document (re-parsed from its own source)
    fulltext: dict[str, str] = {}
    for did, info in docs.items():
        try:
            doc = PdfParser().parse(info["source"])
            fulltext[did] = _norm_title(
                " ".join(l.text for l in doc.lines))
        except Exception:
            fulltext[did] = ""

    # title index of library docs (skip generic OCR/page titles)
    title_index: dict[str, str] = {}
    for did, info in docs.items():
        t = _norm_title(info["title"])
        if t and not info["title"].startswith("Page "):
            title_index[t] = did

    edges: list[dict] = []
    for did, text in fulltext.items():
        for t, target in title_index.items():
            if target == did:
                continue
            if f" {t} " in f" {text} " or f" {t}." in f" {text} ":
                edges.append({"source": did, "target": target})

    return {
        "nodes": [
            {"id": d["id"], "title": d["title"], "chunks": d["chunks"]}
            for d in docs.values()
        ],
        "edges": edges,
    }
