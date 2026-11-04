"""Inspect the textbook's Bibliography page format (read-only, no Chroma)."""
import json
import pymupdf

pdf = r"G:\竞赛\2026传智杯-豆包\pdf\UnderstandingDeepLearning_02_09_26_C.pdf"
out = {}
with pymupdf.open(pdf) as doc:
    # find every page containing a Bibliography heading
    pages_with_bib = []
    for i in range(doc.page_count):
        text = doc[i].get_text()
        if "Bibliography" in text:
            pages_with_bib.append(i)
    out["pages_with_bib"] = pages_with_bib[:5]
    out["bib_page_count"] = len(pages_with_bib)
    target = pages_with_bib[-1] if pages_with_bib else None
    out["bib_page"] = target
    if target is not None:
        lines = doc[target].get_text().splitlines()
        out["first_25_lines"] = lines[:25]
        # count lines that look like [N]-prefixed references
        import re
        cnt = 0
        samples = []
        for ln in lines:
            if re.match(r"^\[\d{1,3}\]", ln.strip()):
                cnt += 1
                if len(samples) < 5:
                    samples.append(ln.strip()[:120])
        out["bracket_ref_lines"] = cnt
        out["bracket_samples"] = samples
with open(r"G:\竞赛\2026传智杯-豆包\docs\debug_textbook_bib.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("[done]")
