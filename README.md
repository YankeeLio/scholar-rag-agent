# ScholarRAG Agent：全流程科研助手

面向学术场景的"大模型 + Agent"科研助手 Web 应用，覆盖文献智能解析、抗幻觉问答、引用图谱挖掘、版本语义去重等科研核心链路，服务于从文献导入到知识问答的全流程闭环。

> 2026 全国高校 AI 大模型挑战赛（B 组）参赛作品

---

## 项目简介

科研工作者每天面对海量论文、扫描件 PDF、长篇教材，需要一个"能读、能查、不胡说"的助手。本项目以 **PDF 细粒度解析 → 语义索引 → 混合检索 → 证据约束生成 → 引用溯源** 为主链路：

- 上传 PDF（矢量版 / 扫描件 / 541 页教材）即自动解析、切块、入库
- 基于本地 BGE-M3 向量 + BM25 稀疏检索的混合召回
- 调用 DeepSeek 大模型作答，**每条结论强制携带原文出处锚点**，证据不足时明确拒答而非编造
- 库内文档自动建立引用关系图谱，支持可视化浏览
- 同一论文的不同版本（如 arXiv v1 / v7）基于正文语义自动去重并提示

## 功能特性

| 模块 | 能力 |
|---|---|
| 文档解析 | PyMuPDF 行级解析（标题树 / 作者机构 / 摘要 / 表格 / 参考文献）；扫描件自动走 RapidOCR 通道；541 页教材按章节感知切块 |
| 语义去重 | 块级余弦相似度聚合（阈值 0.85），识别同论文不同版本，触发预警并支持一键替换 |
| 抗幻觉 RAG | Dense 0.6 + BM25 0.4 混合检索；Prompt 约束"只依据证据回答 / 数字必须与证据一致 / 用提问者语言"；流式输出 + 引用列表 |
| 引用图谱 | 库内文档全文标题匹配建边，前端 ECharts 力导向可视化 |
| Web 界面 | 文献库管理、上传-去重-替换、流式问答（SSE）、引用证据面板、图谱浏览，均由 FastAPI 单页托管 |

## 技术架构

```
浏览器 (apps/web/index.html, ECharts)
        │  HTTP / SSE
FastAPI (apps/api/app/main.py)
   ├─ parser.py    行级结构化解析（章节树 / 参考文献 / 表格）
   ├─ ocr.py       RapidOCR 扫描件通道（onnxruntime CPU）
   ├─ chunker.py    章节感知切块（1800 字符上限，锚点定位）
   ├─ embedding.py 本地 BGE-M3（CPU，1024 维）
   ├─ indexer.py   Chroma 持久化向量库
   ├─ retriever.py 稠密 + BM25 混合检索（中文二元组分词）
   ├─ dedup.py      块级语义去重（avg pairwise cosine）
   ├─ llm.py        DeepSeek Chat 证据约束 RAG（非流式 + SSE）
   └─ graph.py      引用关系图谱构建
```

- **后端**：Python 3.13 + FastAPI + Uvicorn
- **Embedding**：BAAI/bge-m3（本地 CPU 推理，无需 GPU）
- **向量库**：Chroma（持久化到本地磁盘）
- **大模型**：DeepSeek-Chat（OpenAI 兼容接口）
- **OCR**：RapidOCR + ONNX Runtime（CPU）
- **前端**：原生 HTML + ECharts（CDN 降级列表兜底）

## 目录结构

```
├── apps/
│   ├── api/                FastAPI 后端
│   │   ├── app/            核心模块（见上方架构图）
│   │   ├── requirements.txt
│   │   └── .env           环境变量（不入仓库，从 .env.example 复制）
│   └── web/                前端单页
├── pdf/                    官方测试集（4 个 PDF）
├── scripts/                验证与工具脚本
├── docs/                   开发日志、验证产物、接口探针
├── data/                   运行时数据（向量缓存 / Chroma 索引 / 上传副本，不入仓库）
├── .env.example            环境变量模板
└── PLAN.md                 开发计划
```

## 快速开始

### 环境要求

- Python 3.13（已验证）
- Windows / macOS / Linux 均可（无 GPU 要求，CPU 即可）
- 一个 DeepSeek API Key（https://platform.deepseek.com）

### 安装

```powershell
cd apps/api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

首次启动会自动从 HuggingFace 镜像下载 BGE-M3 模型（约 2.2GB）到 `data/hf_cache`。

### 配置

```powershell
Copy-Item .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY
```

### 启动

```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8010
```

- 界面：http://127.0.0.1:8010
- 接口文档（Swagger）：http://127.0.0.1:8010/docs

### 验证用例

将 `pdf/` 目录下的测试文件通过界面或 `/api/documents/upload` 上传：

| 文件 | 验证点 |
|---|---|
| `1706.03762v7.pdf` | 标准双栏论文解析（27 块） |
| `1706.03762v1.pdf` | 与 v7 的语义去重（实测相似度 0.8989，触发预警） |
| `1706.03762v1_img.pdf` | 无文本层扫描件 OCR 解析（28 块，识别质量人工抽检通过） |
| `UnderstandingDeepLearning_02_09_26_C.pdf` | 541 页长书（893 块，章节树含 12 Transformers / 18 Diffusion / 19 RL） |

## 环境变量

| 变量 | 说明 |
|---|---|
| `DEEPSEEK_API_KEY` | DeepSeek 平台密钥 |
| `DEEPSEEK_BASE_URL` | 默认 `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` | 默认 `deepseek-chat` |

## 开发记录

完整开发过程、踩坑记录（含 Chroma 索引损坏事故与恢复流程）见 [`docs/DEVLOG.md`](docs/DEVLOG.md)。

## 团队

- 开发：YankeeLio（B 组参赛选手）
