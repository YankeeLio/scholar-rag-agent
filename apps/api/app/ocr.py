"""ocr.py: OCR fallback for scanned PDFs (no text layer).

Official use case: 1706.03762v1_img.pdf — 15 pages rendered as images.
RapidOCR (onnxruntime, CPU) reads each page; text is rebuilt into a
Document so the standard parse -> chunk -> index pipeline can run.
"""
from __future__ import annotations

import time
from pathlib import Path

from app.parser import Document


class OcrEngine:
    def __init__(self, dpi: int = 200) -> None:
        from rapidocr import RapidOCR
        self.dpi = dpi
        self._engine = RapidOCR()

    # ------------------------------------------------------------------
    def ocr_pdf(self, pdf_path, on_progress=None) -> list[list[str]]:
        """OCR every page; returns per-page line lists."""
        import numpy as np
        import pymupdf

        t0 = time.time()
        pages: list[list[str]] = []
        with pymupdf.open(str(pdf_path)) as doc:
            total = doc.page_count
            for i, page in enumerate(doc):
                pix = page.get_pixmap(dpi=self.dpi)
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                    pix.height, pix.width, pix.n)
                result = self._engine(img)
                lines = list(result.txts) if result and result.txts else []
                pages.append(lines)
                if on_progress:
                    on_progress(i + 1, total)
        return pages

    # ------------------------------------------------------------------
    def ocr_to_document(self, pdf_path) -> Document:
        """Rebuild a Document from OCR text (one Section per page)."""
        from app.parser import Line, Section

        pages = self.ocr_pdf(pdf_path)
        lines: list[Line] = []
        sections: list[Section] = []
        for i, page_lines in enumerate(pages):
            p = i + 1
            sections.append(Section(level=1, number="", title=f"Page {p}",
                                    page=p, y0=0.0))
            for ln in page_lines:
                lines.append(Line(page=p, bbox=[0.0, 0.0, 0.0, 0.0], text=ln,
                                  font_size=10.0, font="", ref_ids=[]))
        # best-effort real title: first non-empty line of page 1
        title = Path(pdf_path).stem
        if pages and pages[0]:
            for ln in pages[0]:
                if ln.strip() and not ln.startswith("arXiv:"):
                    title = ln.strip()
                    break
        return Document(
            source=str(pdf_path),
            pages=len(pages),
            title=title,
            authors=[],
            abstract="",
            lines=lines,
            sections=sections,
            references=[],
            tables=[],
        )
