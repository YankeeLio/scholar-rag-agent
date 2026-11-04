"""Day1: verify torch/sentence-transformers imports and CUDA availability.

stdout capture is unreliable on this host, so results are written to
docs/env_verify.json.
"""
import json

import sentence_transformers
import torch

result = {
    "torch": torch.__version__,
    "cuda_available": bool(torch.cuda.is_available()),
    "device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
    "cuda_device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    "sentence_transformers": sentence_transformers.__version__,
}
with open(r"G:\竞赛\2026传智杯-豆包\docs\env_verify.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
