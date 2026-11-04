"""Day2: verify chunker on v1 (paper) and the 541-page textbook.

Writes results to docs/chunker_verify.json (stdout unreliable on host).
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, r"G:\竞赛\2026传智杯-豆包\apps\api")
from app.chunker import Chunker  # noqa: E402
from app.parser import PdfParser  # noqa: E402

PDFS = {
    "v1": r"G:\竞赛\2026传智杯-豆包\pdf\1706.03762v1.pdf",
    "book": r"G:\竞赛\2026传智杯-豆包\pdf\UnderstandingDeepLearning_02_09_26_C.pdf",
}

results = {}
for name, path in PDFS.items():
    t0 = time.time()
    doc = PdfParser().parse(path)
    parse_t = time.time() - t0
    t0 = time.time()
    chunks = Chunker().chunk(doc)
    chunk_t = time.time() - t0

    sizes = [len(c.text) for c in chunks]
    by_section: dict[str, int] = {}
    for c in chunks:
        by_section[c.section] = by_section.get(c.section, 0) + 1

    results[name] = {
        "pages": doc.pages,
        "lines": len(doc.lines),
        "sections_found": len(doc.sections),
        "chunk_count": len(chunks),
        "chunk_chars_min": min(sizes) if sizes else 0,
        "chunk_chars_max": max(sizes) if sizes else 0,
        "chunk_chars_avg": round(sum(sizes) / len(sizes), 1) if sizes else 0,
        "chunks_over_max": sum(1 for s in sizes if s > 1800),
        "parse_secs": round(parse_t, 2),
        "chunk_secs": round(chunk_t, 2),
        "top_sections": sorted(by_section.items(), key=lambda kv: -kv[1])[:10],
    }

Path(r"G:\竞赛\2026传智杯-豆包\docs\chunker_verify.json").write_text(
    json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
