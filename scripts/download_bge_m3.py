"""Download and smoke-test the BGE-M3 embedding model (CPU).

Uses the hf-mirror endpoint and caches the model under the project's
data/ dir (not the C-drive user cache). Writes a result marker file.
"""
import json
import os
import time
from pathlib import Path

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_HOME"] = r"G:\竞赛\2026传智杯-豆包\data\hf_cache"

from sentence_transformers import SentenceTransformer  # noqa: E402

t0 = time.time()
model = SentenceTransformer("BAAI/bge-m3")
load_s = time.time() - t0

t0 = time.time()
vec = model.encode(["Attention is all you need"], normalize_embeddings=True)
enc_s = time.time() - t0

result = {
    "model": "BAAI/bge-m3",
    "load_secs": round(load_s, 1),
    "encode_secs": round(enc_s, 2),
    "dim": len(vec[0]),
    "sample_first10": [round(float(v), 4) for v in vec[0][:10]],
    "cache_dir": r"G:\竞赛\2026传智杯-豆包\data\hf_cache",
}
Path(r"G:\竞赛\2026传智杯-豆包\docs\bge_m3_verify.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
