"""Generate the scanned-image test PDF (1706.03762v1_img.pdf).

Renders each page of the vector PDF to a raster image (150 dpi) and
rebuilds a PDF with NO text layer, mimicking an OCR-only scanned paper.
Writes its verification result to make_scanned_result.json (stdout capture
is unreliable on this host).
"""
import json
import os
import time

import pymupdf

SRC = r"G:\竞赛\2026传智杯-豆包\pdf\1706.03762v1.pdf"
DST = r"G:\竞赛\2026传智杯-豆包\pdf\1706.03762v1_img.pdf"
RESULT = r"G:\竞赛\2026传智杯-豆包\scripts\make_scanned_result.json"
DPI = 144
JPG_QUALITY = 80

t0 = time.time()
src = pymupdf.open(SRC)
out = pymupdf.open()
for page in src:
    pix = page.get_pixmap(dpi=DPI)
    img_bytes = pix.tobytes("jpeg", jpg_quality=JPG_QUALITY)
    new_page = out.new_page(width=page.rect.width, height=page.rect.height)
    new_page.insert_image(new_page.rect, stream=img_bytes)
out.save(DST)
page_count = out.page_count
out.close()
src.close()
gen_secs = round(time.time() - t0, 1)

# Verify: no text layer in the scanned copy
check = pymupdf.open(DST)
text_pages = [i for i in range(check.page_count) if check[i].get_text().strip()]
check.close()

result = {
    "rendered_pages": page_count,
    "generated_secs": gen_secs,
    "pages_with_text_layer": len(text_pages),
    "scanned_file_bytes": os.path.getsize(DST),
}
with open(RESULT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
