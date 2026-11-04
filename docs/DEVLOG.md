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

---

## Day 2（2026-11-04）

### 完成项

| 项 | 结果 | 验证方式 |
|---|---|---|
| git 仓库 | main 分支初始化，identity YankeeLio，.gitignore 排除 .venv/.env/data | 提交 b5182ff / 53bae4e |
| 结构化解析 parser.py | 行级粒度（page/bbox/字号/字体）；标题/作者/摘要启发式；章节树支持内联编号 + arXiv 独立编号行配对；参考文献独立条目；表格仅收 "Table N:" 题注；行级引用号 | parser_verify.json：v1/v7 均命中标题、8 位作者、1–7 章节树、refs 36/40、表格 4，解析约 0.3s |
| 切块器 chunker.py | 按章节边界分组（bisect），超长章节按 1800 字符拆块；每块携带 doc_id/section/pages/start_line/end_line/ref_ids 锚点 | chunker_verify.json：v1=27 块（max 1799，0 超限）；541 页教材=893 块、解析 6.9s + 切块 0.27s |
| BGE-M3 + Chroma 索引 | BAAI/bge-m3 本地 CPU（1024 维），模型缓存 data/hf_cache（hf-mirror，2.19GB）；Chroma 持久化 data/chroma，cosine 度量 | index_verify.json：27 块入库；β1/β2、8GPU×3.5 天、BLEU 28.4 三问全部命中且带页码/行号锚点，单查 0.3–0.6s |
| FastAPI 骨架 | main.py：/health、上传（解析→切块→索引）、文档列表/详情、语义检索；QA 接口暂返回检索证据（Key 未配置） | api_health/upload/probe2 json：上传 v1 返回完整结构化 + 27 块入库；搜索命中带锚点 |

### Day 2 关键决策与坑

1. **BGE-M3 下载**：huggingface_hub 直连卡死（0 字节），改 hf-mirror 经 WebClient 测速正常（≈4–5 MB/s）；实际 huggingface_hub 后台最终下载成功（2.19GB，加载 203s 首次 / 40s 缓存命中）。
2. **config 路径层级 bug**：ROOT_DIR 误算为 apps/，导致模型在错误目录重复下载 2.2GB → 修正为 `API_DIR.parents[2]`，删除重复目录。
3. **端口冲突**：8000 被本机其他进程占用（PID 3104，未动），开发期改用 8010。
4. **解析启发式迭代**：作者误收标题（改为 title 后、Abstract 前采集）、"3.5 days." 被当章节（要求标题以 ASCII 字母开头且不以句点结尾）、页眉 arXiv 行混入章节树（显式排除）。
5. **Chroma metadata 限制**：仅接受 str/int/float/bool，pages/ref_ids 序列化为逗号字符串。

### 待办（依赖选手）

- [ ] 报名缴费（11-18 截止，最紧急）
- [ ] DeepSeek API Key → 填入 `apps/api/.env`（.env.example 已更新完整模板）
- [ ] GitHub Public 仓库建立

### Day 3 计划

1. DeepSeek 接入（openai SDK + 流式 SSE），QA 接口启用 LLM 生成 + 引用渲染
2. 混合检索升级：BM25（稀疏）+ 向量（稠密）加权融合
3. 语义去重（v1 vs v7）与版本差异摘要
4. 前端骨架（apps/web）：文档列表 + 问答面板 + 溯源高亮

---

## Day 3（2026-11-04 续）

### 完成项

| 项 | 结果 | 验证方式 |
|---|---|---|
| DeepSeek 流式 QA（任务10，9f46904） | llm.py 证据约束提示词（仅依据证据+[n]引用+证据不足明说）；/api/qa 非流式 + /api/qa/stream SSE（citations→delta→done） | llm_verify.json / api_qa_probe.json：big 模型 8×P100、3.5 天、WMT2014 回答正确带 [1]；流式事件流 3561 字节正常 |
| 语义去重 v1/v7（任务12，2b9e1a0） | dedup.py 块级 max-pairwise cosine 平均；阈值首测 0.90 未触发（实测 0.8989）→ 降到 0.85；上传触发默认不入库 + 版本建议；?replace=true 删旧入库 | api_dedup_probe/replace_probe.json：v1 库中传 v7 → 预警"v7 较新建议替换"、indexed:false；replace 后 index 27 |
| 前端骨架（任务13） | apps/web/index.html 单页挂载 FastAPI 根路径（8010/ 即界面）：文献库+上传（去重可一键替换）、SSE 流式问答、引用 [n] 点击看证据原文、健康状态轮询 | root 200/13379 字节；流式接口端到端通过 |
| 混合检索 BM25+向量（任务11，feb0082） | retriever.py：稠密 0.6 + 稀疏 0.4 加权融合；BM25 懒构建（rank-bm25 + jieba 二元组中文分词） | hybrid_verify.json：GPU/天/BLEU 术语问题 sparse 通道提升 top1；optimizer 中文问题端到端回答正确（Adam, β1=0.9, β2=0.98 [4] 指向 §5 原文） |

### Day 3 关键决策与坑

1. **去重阈值**：0.90 首测未触发——v1 vs v7 实测 avg max-pairwise 相似度恰好 0.8989；降到 0.85（无关论文通常 <0.7），官方用例一次通过。
2. **混合检索中英差异**：中文问题对英文文档的 BM25 稀疏侧弱，靠稠密通道兜底；1800 字符大块稀释稠密相似度（optimizer 块排 top4 但 QA top_k=5 仍覆盖）——块长优化列入 Day 4。
3. **服务端口与启动**：沿用 8010；netstat 找 LISTENING PID + Stop-Process（TaskStop 不可靠）。
4. **前端交付形态**：StaticFiles 挂载 "/" 放最后，避免吞掉 API 路由；用户浏览器打开 http://127.0.0.1:8010 即完整界面。

### 待办（依赖选手）

- [ ] 报名缴费（11-18 截止，最紧急）
- [ ] GitHub Public 仓库建立
- [ ] DeepSeek Key 已配置（.env 35 位，llm_configured=true）

### Day 4 计划

1. 541 页教材入库（893 块 CPU 索引约 40–70 分钟，后台跑）+ 教材 RAG 质量验证
2. 扫描件 v1_img OCR 通道（官方用例：图片型 PDF 无文本层）
3. 块长优化（1800 → 1000 左右）重索引评估（仅测试文档先行）
4. 引用图谱 NetworkX + 前端可视化
5. 前端增强：版本去重差异提示、证据面板交互完善


