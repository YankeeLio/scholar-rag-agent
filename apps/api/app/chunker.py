"""Chunker: section-aware chunking of parsed documents.

Groups lines by section boundaries (from the parser's heading tree),
then splits oversized sections into smaller chunks while preserving
line-index ranges so RAG can trace answers back to page + line anchors.
"""
from __future__ import annotations

import bisect
import hashlib
from dataclasses import dataclass, field

from app.parser import Document, Line

DEFAULT_MAX_CHARS = 1800  # ~400 tokens, keeps recall precise


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    section: str
    text: str
    pages: list[int]
    start_line: int
    end_line: int  # exclusive
    ref_ids: list[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "section": self.section,
            "pages": self.pages,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "ref_ids": self.ref_ids,
        }


class Chunker:
    """Split a Document into section-aware chunks with line anchors."""

    def __init__(self, max_chars: int = DEFAULT_MAX_CHARS) -> None:
        self.max_chars = max_chars

    def chunk(self, doc: Document) -> list[Chunk]:
        doc_id = self._doc_id(doc.source)
        groups, labels = self._group_by_section(doc)
        chunks: list[Chunk] = []
        for gi, (label, lines, start_idx) in enumerate(groups):
            # merge consecutive lines of the same section
            sub_chunks = self._split_group(
                doc_id=doc_id, section=label, lines=lines,
                start_line=start_idx, group_idx=gi,
            )
            chunks.extend(sub_chunks)
        return chunks

    # ------------------------------------------------------------------
    @staticmethod
    def _doc_id(source: str) -> str:
        return hashlib.md5(source.encode("utf-8")).hexdigest()[:12]

    # ------------------------------------------------------------------
    def _group_by_section(self, doc: Document):
        """Assign each line to its preceding section boundary."""
        marks: list[tuple[int, float, str]] = []
        for s in doc.sections:
            label = f"{s.number} {s.title}" if s.number else s.title
            marks.append((s.page, s.y0, label))

        # frontmatter group first
        groups: list[tuple[str, list[Line], int]] = [("frontmatter", [], 0)]
        labels_list: list[str] = []
        pos = [(m[0], m[1]) for m in marks]
        labels_list = ["frontmatter"] + [m[2] for m in marks]

        current = 0
        for line in doc.lines:
            key = (line.page, line.bbox[1])
            gi = bisect.bisect_right(pos, key)  # 0..len(marks)
            gi = min(gi, len(labels_list) - 1)
            if gi != current:
                # start a new group
                groups.append((labels_list[gi], [], line_idx_of(doc, line)))
                current = gi
            groups[-1][1].append(line)
        return groups, labels_list

    # ------------------------------------------------------------------
    def _split_group(self, doc_id: str, section: str, lines: list[Line],
                     start_line: int, group_idx: int) -> list[Chunk]:
        """Split a section's lines into chunks under max_chars."""
        chunks: list[Chunk] = []
        if not lines:
            return chunks

        buffer: list[Line] = []
        buf_chars = 0
        sub = 0

        def flush() -> None:
            nonlocal sub
            if not buffer:
                return
            text = "\n".join(l.text for l in buffer)
            pages = sorted({l.page for l in buffer})
            refs: set[int] = set()
            for l in buffer:
                refs.update(l.ref_ids)
            chunks.append(Chunk(
                chunk_id=f"{doc_id}-{group_idx:03d}-{sub:03d}",
                doc_id=doc_id,
                section=section,
                text=text,
                pages=pages,
                start_line=start_line + line_offset,
                end_line=start_line + line_offset + len(buffer),
                ref_ids=sorted(refs),
            ))
            sub += 1

        line_offset = 0
        for line in lines:
            ln = len(line.text) + 1
            if buffer and buf_chars + ln > self.max_chars:
                flush()
                line_offset += len(buffer)
                buffer = []
                buf_chars = 0
            buffer.append(line)
            buf_chars += ln
        flush()
        return chunks


def line_idx_of(doc: Document, target: Line) -> int:
    """Return the original index of a Line inside doc.lines (by identity)."""
    for i, l in enumerate(doc.lines):
        if l is target:
            return i
    return 0
