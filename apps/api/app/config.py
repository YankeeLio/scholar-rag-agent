"""Central configuration for the API app.

Values come from environment variables (apps/api/.env, see .env.example)
with sensible local defaults.
"""
from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # dotenv optional; env vars can be set manually
    load_dotenv = None

# project root: <repo>/apps/api/app -> <repo>
API_DIR = Path(__file__).resolve().parent
ROOT_DIR = API_DIR.parents[2]
ENV_FILE = API_DIR.parent / ".env"  # apps/api/.env

if load_dotenv is not None:
    load_dotenv(ENV_FILE)


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


def _env_path(name: str, default: Path) -> Path:
    """Resolve a configured path; relative values anchor to the project root."""
    v = os.environ.get(name, "")
    if not v:
        return default
    p = Path(v)
    return p if p.is_absolute() else (ROOT_DIR / p)


# --- paths -------------------------------------------------------------
DATA_DIR = _env_path("DATA_DIR", ROOT_DIR / "data")
VECTOR_DIR = _env_path("VECTOR_DIR", DATA_DIR / "chroma")
HF_HOME = _env_path("HF_HOME", DATA_DIR / "hf_cache")
PDF_DIR = _env_path("PDF_DIR", ROOT_DIR / "pdf")

# --- embedding ---------------------------------------------------------
BGE_MODEL_NAME = _env("BGE_MODEL_NAME", "BAAI/bge-m3")
EMBEDDING_DEVICE = _env("EMBEDDING_DEVICE", "cpu")  # CUDA unavailable locally

# --- LLM (DeepSeek) ----------------------------------------------------
LLM_API_KEY = _env("DEEPSEEK_API_KEY", "")
LLM_BASE_URL = _env("LLM_BASE_URL", "https://api.deepseek.com")
LLM_CHAT_MODEL = _env("LLM_CHAT_MODEL", "deepseek-chat")
LLM_REASON_MODEL = _env("LLM_REASON_MODEL", "deepseek-reasoner")

# --- service -----------------------------------------------------------
API_HOST = _env("API_HOST", "127.0.0.1")
API_PORT = int(_env("API_PORT", "8000"))

CHUNK_MAX_CHARS = int(_env("CHUNK_MAX_CHARS", "1800"))
RETRIEVAL_TOP_K = int(_env("RETRIEVAL_TOP_K", "5"))
