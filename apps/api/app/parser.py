"""PdfParser: structured parsing of academic PDF papers.

Design decisions (validated on 1706.03762 Day 1):
- Work at LINE granularity (PyMuPDF blocks mix two-column text into one
  bounding box, destroying column reconstruction and citation anchors).
- Title detection via font-size heuristic on page 1, excluding arXiv
  header lines.
- arXiv layout support: section numbers ("1") and titles ("Introduction")
  often live on SEPARATE lines, so the section detector pairs them.
- References collected as standalone entries after the References heading.
- Tables detected only by "Table N:" captions (avoids body sentences like
  "Table 2 summarizes ...").

Every line carries page + bbox + font info so downstream RAG can cite
page-level evidence precisely (Source Tracing).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf

# Reference entry: "[12] Author, Title, ..."
REF_RE = re.compile(r"^\[(\d{1,3})\]\s*(.*)$")
# Section heading with inline number: "2.1 Background"
SECTION_NUM_RE = re.compile(r"^(\d{1,2}(?:\.\d{1,2}){0,2})\s+(.+)$")
# Standalone section number line: "1" / "3.2"
SECTION_NUM_ONLY_RE = re.compile(r"^\d{1,2}(?:\.\d{1,2}){0,2}$")
# Table caption must carry a colon/dot: "Table 1: ..."
TABLE_CAP_RE = re.compile(r"^Table\s+(\d+)\s*[:.]\s*(.*)$", re.IGNORECASE)
# Organization lines inside the author block (skip)
ORG_RE = re.compile(
    r"^(Google Brain|Google Research|Google|University of Toronto|DeepMind|"
    r"Microsoft Research|Facebook AI|IBM Research|Stanford University|"
    r"UC Berkeley|MIT|Carnegie Mellon|ETH Zürich|EPFL|Inria|University of|"
    r"Institute for|Laboratory|Research Center|Amazon|Apple|Meta|OpenAI)",
    re.IGNORECASE,
)
# Font size used to separate headings from body text (11.5+ on arXiv)
HEADING_FONT_SIZE = 11.0


@dataclass
class Line:
    """A single visual line of text with precise position metadata."""

    page: int
    bbox: list[float]  # [x0, y0, x1, y1]
    text: str
    font_size: float
    font: str
    ref_ids: list[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "page": self.page,
            "bbox": self.bbox,
            "text": self.text,
            "font_size": round(self.font_size, 1),
            "font": self.font,
            "ref_ids": self.ref_ids,
        }


@dataclass
class Section:
    level: int
    number: str
    title: str
    page: int
    y0: float


@dataclass
class Reference:
    id: int
    text: str
    page: int


@dataclass
class Table:
    caption: str
    page: int


@dataclass
class Document:
    """Structured representation of one parsed paper."""

    source: str
    pages: int
    title: str
    authors: list[str]
    abstract: str
    lines: list[Line]
    sections: list[Section]
    references: list[Reference]
    tables: list[Table]

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "pages": self.pages,
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "line_count": len(self.lines),
            "sections": [s.__dict__ for s in self.sections],
            "references": [r.__dict__ for r in self.references],
            "tables": [t.__dict__ for t in self.tables],
        }


class PdfParser:
    """Extract a structured Document from a vector PDF."""

    def parse(self, pdf_path: str | Path) -> Document:
        doc = pymupdf.open(str(pdf_path))
        lines: list[Line] = []
        for pno in range(doc.page_count):
            page = doc[pno]
            lines.extend(self._extract_lines(page, pno))

        title, authors, abstract, body_start = self._parse_front_matter(lines)
        sections = self._detect_sections(lines, body_start)
        references = self._collect_references(lines)
        tables = self._collect_tables(lines)
        self._attach_ref_ids(lines, references)

        result = Document(
            source=str(pdf_path),
            pages=doc.page_count,
            title=title,
            authors=authors,
            abstract=abstract,
            lines=lines,
            sections=sections,
            references=references,
            tables=tables,
        )
        doc.close()
        return result

    # ------------------------------------------------------------------
    @staticmethod
    def _extract_lines(page: pymupdf.Page, pno: int) -> list[Line]:
        """Extract per-line data with position + font metadata."""
        out: list[Line] = []
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if block.get("type") != 0:  # skip images
                continue
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                if not spans:
                    continue
                text = "".join(s["text"] for s in spans).strip()
                if not text:
                    continue
                bbox = [round(v, 1) for v in line["bbox"]]
                size = max(s["size"] for s in spans)
                font = spans[0]["font"]
                out.append(Line(page=pno, bbox=bbox, text=text,
                                font_size=size, font=font))
        return out

    # ------------------------------------------------------------------
    @staticmethod
    def _parse_front_matter(lines: list[Line]):
        """Detect title, authors and abstract from page-1 heuristics.

        Returns (title, authors, abstract, body_start_index).
        """
        title, authors, abstract = "", [], ""
        body_start = 0
        page1 = [l for l in lines if l.page == 0]
        if not page1:
            return title, authors, abstract, body_start

        # --- Title: largest font line, excluding arXiv/header lines ---
        candidates = [l for l in page1 if not l.text.startswith("arXiv:")]
        if candidates:
            title_line = max(candidates, key=lambda l: l.font_size)
            title = title_line.text

        # --- Authors: lines between title and Abstract ---
        in_author_zone = False
        for l in page1:
            t = l.text.strip()
            if not t:
                continue
            if not in_author_zone:
                if t == title:
                    in_author_zone = True
                continue
            # stop at Abstract heading
            if t.lower() in ("abstract",) or t.lower().startswith("abstract "):
                break
            if "@" in t or ORG_RE.match(t) or re.match(r"^\d+$", t):
                continue
            if re.search(r"[A-Za-z]", t):
                authors.append(t)
        seen: set[str] = set()
        clean: list[str] = []
        for a in authors:
            if a not in seen:
                seen.add(a)
                clean.append(a)
        authors = clean[:12]

        # --- Abstract: text between Abstract and the next heading ---
        abstract_lines: list[str] = []
        in_abs = False
        for idx, l in enumerate(lines):
            t = l.text.strip().lower()
            if not in_abs:
                if t == "abstract":
                    in_abs = True
                continue
            # stop conditions: Introduction heading (numbered or not),
            # standalone section number, or any larger-font heading line
            if (
                t in ("introduction", "1 introduction", "references")
                or t == "1"
                or (
                    l.font_size >= HEADING_FONT_SIZE
                    and len(l.text) < 60
                    and re.match(r"^[A-Za-z]", l.text.strip())
                )
            ):
                body_start = idx
                break
            abstract_lines.append(l.text)
        abstract = " ".join(abstract_lines).strip()
        return title, authors, abstract, body_start

    # ------------------------------------------------------------------
    @staticmethod
    def _detect_sections(lines: list[Line], body_start: int) -> list[Section]:
        """Build the heading tree from numbered and unnumbered headings.

        Handles both inline numbers ("2.1 Background") and the arXiv
        layout where "1" and "Introduction" are separate lines.
        """
        sections: list[Section] = []
        i = body_start
        n = len(lines)
        while i < n:
            l = lines[i]
            t = l.text.strip()

            # 1) Inline numbered heading: "2.1 Background"
            m = SECTION_NUM_RE.match(t)
            title_part = m.group(2).strip() if m else ""
            if (m and len(t) < 100
                    and re.search(r"[A-Za-z]", title_part)
                    and len(title_part) >= 3
                    and not title_part.endswith(".")):
                sections.append(Section(
                    level=m.group(1).count(".") + 1,
                    number=m.group(1),
                    title=m.group(2).strip(),
                    page=l.page, y0=l.bbox[1],
                ))

            # 2) Standalone number + heading on the next line (arXiv)
            elif (SECTION_NUM_ONLY_RE.match(t)
                  and l.font_size >= HEADING_FONT_SIZE
                  and i + 1 < n):
                nxt = lines[i + 1]
                nt = nxt.text.strip()
                if (nxt.page == l.page
                        and nxt.font_size >= HEADING_FONT_SIZE
                        and len(nt) < 60
                        and re.match(r"^[A-Za-z]", nt)):
                    sections.append(Section(
                        level=1, number=t, title=nt,
                        page=l.page, y0=l.bbox[1],
                    ))
                    i += 1  # consume the heading line too

            # 3) Unnumbered heading: "References", "Introduction"
            elif (l.font_size >= HEADING_FONT_SIZE
                  and 0 < len(t) < 60
                  and re.match(r"^[A-Za-z]", t)
                  and not t.startswith("arXiv:")):
                sections.append(Section(level=1, number="", title=t,
                                        page=l.page, y0=l.bbox[1]))
            i += 1
        return sections

    # ------------------------------------------------------------------
    @staticmethod
    def _collect_references(lines: list[Line]) -> list[Reference]:
        """Collect [n] entries after the References heading."""
        refs: list[Reference] = []
        in_refs = False
        for l in lines:
            t = l.text.strip()
            if t.lower() in ("references", "bibliography"):
                in_refs = True
                continue
            if in_refs:
                m = REF_RE.match(t)
                if m:
                    refs.append(Reference(id=int(m.group(1)),
                                          text=m.group(2).strip(),
                                          page=l.page))
        return refs

    # ------------------------------------------------------------------
    @staticmethod
    def _collect_tables(lines: list[Line]) -> list[Table]:
        """Collect tables from "Table N:" captions only."""
        tables: list[Table] = []
        for l in lines:
            m = TABLE_CAP_RE.match(l.text.strip())
            if m:
                tables.append(Table(
                    caption=m.group(2).strip() or f"Table {m.group(1)}",
                    page=l.page,
                ))
        return tables

    # ------------------------------------------------------------------
    @staticmethod
    def _attach_ref_ids(lines: list[Line], refs: list[Reference]) -> None:
        """Attach citation numbers like [12] to the containing line."""
        for l in lines:
            ids: list[int] = []
            for m in re.finditer(r"\[(\d{1,3})\](\s*[-–,]\s*\[\d{1,3}\])?", l.text):
                ids.append(int(m.group(1)))
            l.ref_ids = sorted(set(ids))
