"""rebuild_index.py: recover from Chroma HNSW corruption.

Reads chunk texts + metadata out of the surviving sqlite, wipes the
corrupted chroma dir, re-embeds locally and rebuilds the collection.

Run with the server STOPPED (no other process may open data/chroma).
"""
from __future__ import annotations

import json
import shutil
import sqlite3
import sys
from pathlib import Path

ROOT = Path(r"G:\竞赛\2026传智杯-豆包")
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.config import VECTOR_DIR  # noqa: E402

CHROMA_DIR = VECTOR_DIR
DB = CHROMA_DIR / "chroma.sqlite3"


def extract_chunks() -> tuple[list[str], list[dict], list[str]]:
    con = sqlite3.connect(str(DB))
    cur = con.cursor()

    # texts from FTS content
    cur.execute("SELECT id, c0 FROM embedding_fulltext_search_content")
    texts: dict[int, str] = {i: t or "" for i, t in cur.fetchall()}

    # metadata key-value
    cur.execute("SELECT id, key, string_value, int_value, float_value, bool_value "
                "FROM embedding_metadata")
    meta: dict[int, dict] = {}
    for i, k, sv, iv, fv, bv in cur.fetchall():
        v = sv if sv is not None else (iv if iv is not None
                                       else (fv if fv is not None else bv))
        meta.setdefault(i, {})[k] = v

    # ids order (embeddings table)
    cur.execute("SELECT id, embedding_id FROM embeddings ORDER BY id")
    rows = cur.fetchall()
    con.close()

    ids, metas, texts_out = [], [], []
    for i, eid in rows:
        if i not in texts or not texts[i]:
            continue
        m = meta.get(i, {})
        # drop Chroma reserved internal keys (would be rejected on add)
        m = {k: v for k, v in m.items() if not k.startswith("chroma:")}
        ids.append(str(eid))
        metas.append(m)
        texts_out.append(texts[i])
    return ids, metas, texts_out


def main() -> None:
    print(f"[1/4] extracting chunks from {DB}")
    ids, metas, texts = extract_chunks()
    print(f"      extracted {len(texts)} chunks")
    doc_ids = {m.get("doc_id") for m in metas}
    print(f"      docs: {sorted(doc_ids)}")

    # wipe corrupted dir
    print("[2/4] wiping corrupted chroma dir")
    shutil.rmtree(str(CHROMA_DIR), ignore_errors=True)

    print("[3/4] re-embedding + rebuilding collection (CPU, please wait)")
    import numpy as np
    from app.embedding import EmbeddingService
    from app.indexer import VectorIndex

    emb_cache = ROOT / "docs" / "_embed_cache.npy"
    emb = EmbeddingService()
    emb._ensure_model()
    if emb_cache.exists():
        print(f"      loading cached embeddings from {emb_cache.name}")
        vecs = np.load(str(emb_cache)).tolist()
    else:
        vecs = emb.embed_documents(texts)
        np.save(str(emb_cache), np.array(vecs))
        print(f"      embeddings cached to {emb_cache.name}")

    idx = VectorIndex()
    idx.collection.add(
        ids=ids,
        documents=texts,
        metadatas=metas,
        embeddings=vecs,
    )
    print(f"      collection now has {idx.count()} chunks")

    print("[4/4] done.")
    summary = {"chunks": len(texts), "docs": sorted(doc_ids),
               "index_count": idx.count()}
    (ROOT / "docs" / "rebuild_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
