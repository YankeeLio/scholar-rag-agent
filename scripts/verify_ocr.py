"""Probe OCR on the first pages of the scanned v1_img."""
import json
import sys
import time

sys.path.insert(0, r"G:\竞赛\2026传智杯-豆包\apps\api")
from app.ocr import OcrEngine  # noqa: E402

eng = OcrEngine()
t0 = time.time()
lines = eng.ocr_pdf(r"G:\竞赛\2026传智杯-豆包\pdf\1706.03762v1_img.pdf",
                    on_progress=lambda done, total: print(f"page {done}/{total}"))
out = {
    "pages": len(lines),
    "lines_per_page": [len(p) for p in lines],
    "elapsed_s": round(time.time() - t0, 1),
    "page1_head": lines[0][:25] if lines and lines[0] else [],
    "page2_head": lines[1][:25] if len(lines) > 1 and lines[1] else [],
}
with open(r"G:\竞赛\2026传智杯-豆包\docs\ocr_probe.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("[done] wrote docs/ocr_probe.json")
