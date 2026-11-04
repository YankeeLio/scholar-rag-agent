# 开发日志

## Day 1（2026-11-03）

### 完成项

| 项 | 结果 | 验证方式 |
|---|---|---|
| 项目骨架 | `G:\竞赛\2026传智杯-豆包`（apps/api + .venv、apps/web、scripts、docs、pdf） | 目录清单 |
| 核心依赖 | PyMuPDF 2.1 / FastAPI 0.162 / NetworkX 3.7 / torch 2.15.0+cpu / sentence-transformers 6.2.0 | import 验证（env_verify.json） |
| PDF 解析验证（v1） | 15 页；标题"Attention Is All You Need"识别；Table 1/2/3 命中；文本 3.58 万字符；耗时 0.24s | parse_probe.py |
| 扫描版生成 | 1706.03762v1_img.pdf：15 页、无文本层、3.2MB、耗时 2.0s | make_scanned.py + make_scanned_result.json |
| 算力决策 | **CUDA 不可用**（nvidia-smi 缺失、驱动条目缺失、torch.cuda=False）→ Embedding 走本地 CPU BGE-M3 保底 | gpu_detect.json + env_verify.json |

### 环境决策记录

1. **Embedding 通道**：`EMBEDDING_MODE=local`（CPU BGE-M3）。若用户日后安装 NVIDIA 驱动，可升级 CUDA 版 torch 提速，非必需。
2. **本机 stdout 捕获不可靠**：所有 python 验证脚本统一"写结果文件 → 读取"模式（*_result.json / *_detect.json），避免依赖 stdout。
3. **PyMuPDF API**：用 `import pymupdf`（fitz 已弃用警告）。
4. **Python 3.13 兼容性**：pymupdf/fastapi/torch-cpu/sentence-transformers/networkx 全部装通；chromadb 待验证（Day 2 前）。

### 官方测试集就绪（4/4）

| 文件 | 大小 | 来源 |
|---|---|---|
| 1706.03762v1.pdf | 2.0MB | arXiv |
| 1706.03762v7.pdf | 2.1MB | arXiv |
| UnderstandingDeepLearning_02_09_26_C.pdf | 21.3MB | udlbook GitHub Releases |
| 1706.03762v1_img.pdf | 3.2MB | 本机生成（144dpi JPEG 80） |

### 待办（依赖选手）

- [ ] 报名缴费（11-18 截止，最紧急）
- [ ] DeepSeek API Key → 填入 `apps/api/.env`（模板已建 .env.example）
- [ ] 安装 git（GitHub 提交必需）
- [ ] GitHub Public 仓库建立

### Day 2 计划

1. 验证 chromadb 在 Python 3.13 可用
2. 标题感知切块器（保留公式/表格/引用号）
3. BGE-M3 本地加载 + v1 建索引（CPU 计时）
4. 混合检索（向量 + BM25）+ 溯源锚点元数据
5. FastAPI 骨架：上传 / 解析 / 问答接口
