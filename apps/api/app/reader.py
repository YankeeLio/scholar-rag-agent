"""reader.py: page-level rendering + layout text for side-by-side reading.

Two capabilities back the "联动阅读" (linked reading) view:
  - render_page(): rasterize one PDF page to PNG (in-memory LRU cache)
  - page_layout(): line-level text with normalized bounding boxes, so the
    frontend can overlay highlights and map a translation block back to
    its exact position on the rendered page image.

Bounding boxes are normalized to 0..1 against the page rect, which keeps
the overlay independent of the render DPI.
"""
from __future__ import annotations

from collections import OrderedDict

import pymupdf


class PageReader:
    def __init__(self, cache_pages: int = 24) -> None:
        self._cache: OrderedDict[tuple, bytes] = OrderedDict()
        self._cache_pages = cache_pages

    # ------------------------------------------------------------------
    def render_page(self, pdf_path: str, page_no: int, dpi: int = 144) -> bytes:
        key = (str(pdf_path), int(page_no), int(dpi))
        hit = self._cache.get(key)
        if hit is not None:
            self._cache.move_to_end(key)
            return hit

        with pymupdf.open(pdf_path) as doc:
            if page_no < 1 or page_no > doc.page_count:
                raise IndexError(
                    f"page {page_no} out of range 1..{doc.page_count}")
            pix = doc[page_no - 1].get_pixmap(dpi=dpi)
            png = pix.tobytes("png")

        self._cache[key] = png
        while len(self._cache) > self._cache_pages:
            self._cache.popitem(last=False)
        return png

    # ------------------------------------------------------------------
    def page_layout(self, pdf_path: str, page_no: int) -> dict:
        with pymupdf.open(pdf_path) as doc:
            if page_no < 1 or page_no > doc.page_count:
                raise IndexError(
                    f"page {page_no} out of range 1..{doc.page_count}")
            page = doc[page_no - 1]
            rect = page.rect
            w = rect.width or 1.0
            h = rect.height or 1.0
            page_count = doc.page_count

            lines: list[dict] = []
            blocks = page.get_text("dict").get("blocks", [])
            for block in blocks:
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    text = "".join(
                        s.get("text", "") for s in line.get("spans", [])
                    ).strip()
                    if not text:
                        continue
                    x0, y0, x1, y1 = line["bbox"]
                    lines.append({
                        "text": text,
                        "bbox": [
                            round(x0 / w, 4), round(y0 / h, 4),
                            round(x1 / w, 4), round(y1 / h, 4),
                        ],
                    })

        return {
            "page": page_no,
            "page_count": page_count,
            "width": round(w, 2),
            "height": round(h, 2),
            "lines": lines,
        }
