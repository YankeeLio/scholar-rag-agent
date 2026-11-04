"""Day2: verify the structured parser on v1 and v7.

Writes results to docs/parser_verify.json (stdout unreliable on host).
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, r"G:\竞赛\2026传智杯-豆包\apps\api")
from app.parser import PdfParser  # noqa: E402

PDFS = {
    "v1": r"G:\竞赛\2026传智杯-豆包\pdf\1706.03762v1.pdf",
    "v7": r"G:\竞赛\2026传智杯-豆包\pdf\1706.03762v7.pdf",
}

results = {}
for name, path in PDFS.items():
    t0 = time.time()
    doc = PdfParser().parse(path)
    dur = time.time() - t0
    results[name] = {
        "pages": doc.pages,
        "title": doc.title,
        "authors": doc.authors,
        "abstract_chars": len(doc.abstract),
        "line_count": len(doc.lines),
        "section_count": len(doc.sections),
        "sections": [f"{s.number} {s.title}" for s in doc.sections[:12]],
        "ref_count": len(doc.references),
        "ref_first": doc.references[0].text[:80] if doc.references else "",
        "table_count": len(doc.tables),
        "tables": [f"p{t.page}: {t.caption[:60]}" for t in doc.tables],
        "parse_secs": round(dur, 2),
    }

out = Path(r"G:\竞赛\2026传智杯-豆包\docs\parser_verify.json")
out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
