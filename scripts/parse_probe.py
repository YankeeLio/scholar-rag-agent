"""Day1 probe: verify PyMuPDF parsing of the official test PDF (1706.03762v1).

Checks: page count, text volume, title detection (font-size heuristic),
reference entries, table mentions, and wall-clock parse time.
"""
import re
import time

import pymupdf

PDF = r"G:\竞赛\2026传智杯-豆包\pdf\1706.03762v1.pdf"

t0 = time.time()
doc = pymupdf.open(PDF)
lines_all: list[str] = []
for page in doc:
    lines_all.extend(page.get_text("text").splitlines())
dur = time.time() - t0

print("pages:", doc.page_count)
print("text_lines:", len(lines_all))
print("chars:", sum(len(l) for l in lines_all))

# Title candidates: largest font spans on page 1
page0 = doc[0]
spans = []
for block in page0.get_text("dict")["blocks"]:
    if block.get("type") != 0:
        continue
    for line in block.get("lines", []):
        for span in line.get("spans", []):
            spans.append((span["size"], span["text"], span["font"]))
top = sorted(spans, key=lambda x: -x[0])[:5]
print("top_font_spans:", [(round(s, 1), t[:60], f) for s, t, f in top])

# Reference entries: lines starting with [n]
refs = [l for l in lines_all if re.match(r"^\[\d+\]\s*\S", l.strip())]
print("ref_entries:", len(refs))

# Table mentions
tables = [l.strip() for l in lines_all if re.search(r"Table \d", l)]
print("table_mentions:", tables[:6])

print("parse_secs:", round(dur, 2))
doc.close()
