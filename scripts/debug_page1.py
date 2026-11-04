"""Debug: dump page-1 line structure and Abstract zone of 1706.03762v1."""
import json
import sys

sys.path.insert(0, r"G:\竞赛\2026传智杯-豆包\apps\api")
from app.parser import PdfParser  # noqa: E402

path = r"G:\竞赛\2026传智杯-豆包\pdf\1706.03762v1.pdf"
lines = PdfParser()._extract_lines(__import__("pymupdf").open(path)[0], 0)

out = {
    "page1_lines": [
        {"i": i, "fs": l.font_size, "text": l.text[:110]}
        for i, l in enumerate(lines)
    ][:40],
    "abstract_zone": [],
}
for i, l in enumerate(lines):
    t = l.text.strip().lower()
    if "abstract" in t or t.startswith("1 introduction") or "introduction" in t[:30]:
        out["abstract_zone"].append({"i": i, "page": l.page, "fs": l.font_size, "text": l.text[:100]})

with open(r"G:\竞赛\2026传智杯-豆包\docs\debug_page1.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
