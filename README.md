# 豆包科研助手（SciLoom · 豆包工作流）

全国高校 AI 大模型挑战赛参赛项目（B 组）的豆包独立开发目录。

> 与 `G:\竞赛\2026年传智杯`（另一工作流）并行，互不干扰。
> 本目录由豆包 Agent 工作流负责开发与维护。

## 当前状态

- 官方测试集：4/4 就绪（含扫描版，已生成）
- 解析链路：PyMuPDF 验证通过（15 页 / 标题 / 表格 / 参考文献 / 0.24s）
- 算力：RTX 3060 Laptop（CUDA 存疑）→ Embedding 走本地 CPU BGE-M3 保底

## 目录结构

```
├── PLAN.md          # 15 天开发执行计划
├── .env.example     # 环境变量模板（DeepSeek Key 填这里，不入库）
├── pdf/             # 官方测试集
├── scripts/         # 验证与工具脚本
├── docs/            # 进度与决策记录
└── apps/
    ├── api/         # FastAPI 后端（.venv 虚拟环境）
    └── web/         # Next.js 前端
```

## 快速开始（Day1 已验证部分）

```powershell
# 解析探测
apps\api\.venv\Scripts\python.exe scripts\parse_probe.py

# 生成扫描版（已生成，可跳过）
apps\api\.venv\Scripts\python.exe scripts\make_scanned.py
```

## 环境变量

复制 `.env.example` 为 `.env`，填入 `DEEPSEEK_API_KEY`。密钥永不入库。
