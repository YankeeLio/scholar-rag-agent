"""Reproduce the OCR-upload flow outside the server to find the 500."""
import json
import sys
import traceback

sys.path.insert(0, r"G:\竞赛\2026传智杯-豆包\apps\api")
from app.chunker import Chunker  # noqa: E402
from app.embedding import EmbeddingService  # noqa: E402
from app.indexer import VectorIndex  # noqa: E402
from app.parser import PdfParser  # noqa: E402

src = r"G:\竞赛\2026传智杯-豆包\pdf\1706.03762v1_img.pdf"
emb = EmbeddingService()
idx = VectorIndex()
out = {}

try:
    doc = PdfParser().parse(src)
    out["parser_title"] = doc.title
    out["parser_sections"] = len(doc.sections)
    out["parser_text_chars"] = sum(len(l) for s in doc.sections for l in s.lines)

    if not doc.sections and not doc.title:
        from app.ocr import OcrEngine
        out["ocr"] = "triggered"
        doc = OcrEngine().ocr_to_document(src)
        out["ocr_title"] = doc.title
        out["ocr_sections"] = len(doc.sections)
        out["ocr_lines"] = len(doc.lines)
        out["ocr_chars"] = sum(len(l.text) for l in doc.lines)

    chunks = Chunker().chunk(doc)
    out["chunk_count"] = len(chunks)
    out["chunk0_section"] = chunks[0].section if chunks else None
    out["chunk0_head"] = chunks[0].text[:80] if chunks else None
    out["status"] = "ok"
except Exception:
    out["status"] = "error"
    out["traceback"] = traceback.format_exc()

with open(r"G:\竞赛\2026传智杯-豆包\docs\debug_ocr_upload.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("[done]")
