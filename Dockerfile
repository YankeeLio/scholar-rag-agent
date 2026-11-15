# ScholarRAG Agent · 全流程科研助手
# 单镜像托管 FastAPI + 前端静态资源；模型在首次启动时从镜像站下载到 /app/data。
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/app/data/hf_cache \
    HF_ENDPOINT=https://hf-mirror.com \
    EMBEDDING_DEVICE=cpu \
    DATA_DIR=/app/data

# OpenCV / ONNXRuntime 运行库（OCR 通道需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 libglib2.0-0 ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 依赖分层：先装 CPU 版 torch，避免拉取 CUDA 版本（体积从数 GB 降到数百 MB）
COPY apps/api/requirements.txt /app/apps/api/requirements.txt
RUN pip install --upgrade pip \
    && pip install torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu \
    && pip install -r /app/apps/api/requirements.txt

COPY apps/api/app /app/apps/api/app
COPY apps/web /app/apps/web
COPY pdf /app/pdf

RUN mkdir -p /app/data/uploads

WORKDIR /app/apps/api
EXPOSE 8010

HEALTHCHECK --interval=30s --timeout=5s --start-period=150s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8010/health || exit 1

# 注意：密钥通过 --env-file / -e 注入，不打进镜像
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8010"]
