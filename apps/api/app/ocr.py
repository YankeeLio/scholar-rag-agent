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
    def ocr_page_lines(self, pdf_path, page_no: int, dpi: int = 200) -> list[dict]:
        """OCR a single scanned page; returns [{text, bbox(normalized)}].

        Used by the linked-reading view so scanned PDFs still get clickable
        line boxes overlaid on the rendered page image.
        """
        import numpy as np
        import pymupdf

        with pymupdf.open(str(pdf_path)) as doc:
            if page_no < 1 or page_no > doc.page_count:
                raise IndexError(
                    f"page {page_no} out of range 1..{doc.page_count}")
            page = doc[page_no - 1]
            pix = page.get_pixmap(dpi=dpi)
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                pix.height, pix.width, pix.n)
            w = float(pix.width) or 1.0
            h = float(pix.height) or 1.0
            result = self._engine(img)

        boxes = getattr(result, "boxes", None) if result else None
        txts = getattr(result, "txts", None) if result else None
        scores = getattr(result, "scores", None) if result else None
        # boxes/scores are numpy arrays: never test their truth value directly
        if boxes is None or txts is None:
            return []
        if len(boxes) == 0 or len(txts) == 0:
            return []

        out: list[dict] = []
        for i, (box, txt) in enumerate(zip(boxes, txts)):
            if txt is None or not str(txt).strip():
                continue
            xs = [float(p[0]) for p in box]
            ys = [float(p[1]) for p in box]
            score = None
            if scores is not None and i < len(scores):
                score = float(scores[i])
            out.append({
                "text": str(txt).strip(),
                "bbox": [round(min(xs) / w, 4), round(min(ys) / h, 4),
                         round(max(xs) / w, 4), round(max(ys) / h, 4)],
                "score": round(score, 3) if score is not None else None,
            })
        return out

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
