# 部署说明（公网演示）

面对赛题要求的「公网在线演示地址」，本文给出最短可用路径。

## 一、服务器要求

| 项 | 建议 | 说明 |
|---|---|---|
| CPU | 4 核 | BGE-M3 为 CPU 推理，2 核会明显卡顿 |
| 内存 | 8 GB | 模型常驻约 2.5–3 GB，2 核 4 GB 容易 OOM |
| 磁盘 | 40 GB | 镜像约 400 MB + 模型缓存约 4.3 GB + 索引与上传件 |
| 系统 | Ubuntu 22.04 / Debian 12 | 本文命令以 Ubuntu 为例 |
| 网络 | 放行 8010 端口 | 云厂商安全组里加一条入方向规则 |

> 若只想临时演示，也可用 2 核 4 GB + 4 GB swap 顶住，但首次索引会很慢。

## 二、方式 A：Docker（推荐）

```bash
# 1. 装 Docker（Ubuntu）
curl -fsSL https://get.docker.com | sh

# 2. 取代码
git clone https://github.com/YankeeLio/scholar-rag-agent.git
cd scholar-rag-agent

# 3. 配置密钥（不要把 .env 提交回仓库）
cp .env.example apps/api/.env
vi apps/api/.env          # 填入 DEEPSEEK_API_KEY

# 4. 构建并启动
docker compose up -d --build

# 5. 等模型下载完成（首次约 5–15 分钟，日志里会显示下载进度）
docker compose logs -f

# 6. 验证
curl http://127.0.0.1:8010/health
```

看到 `{"status":"ok","model_loaded":true,"index_count":...,"llm_configured":true}` 即为就绪。
浏览器访问 `http://<公网IP>:8010`。

## 三、方式 B：不用 Docker（裸机）

```bash
sudo apt update && sudo apt install -y python3.13 python3.13-venv libgl1 libglib2.0-0
cd apps/api
python3.13 -m venv .venv && . .venv/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
cp ../../.env.example .env && vi .env
uvicorn app.main:app --host 0.0.0.0 --port 8010
```

长期运行建议交给 systemd：

```ini
# /etc/systemd/system/scholarrag.service
[Unit]
Description=ScholarRAG Agent
After=network.target

[Service]
WorkingDirectory=/opt/scholar-rag-agent/apps/api
Environment=HF_ENDPOINT=https://hf-mirror.com
ExecStart=/opt/scholar-rag-agent/apps/api/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8010
Restart=always

[Install]
WantedBy=multi-user.target
```

## 四、把本地已建好的索引搬上去（省 40–70 分钟）

本地已经入库了教材 893 块 + 扫描件 28 块。重新索引在 CPU 上要 40–70 分钟，直接搬 `data/` 里的两样东西最快：

```bash
# 在你本机（PowerShell）
scp -r .\data\chroma   root@<IP>:/opt/scholar-rag-agent/data/
scp -r .\data\uploads  root@<IP>:/opt/scholar-rag-agent/data/
```

**不要**搬 `data/hf_cache`（约 4.3 GB 模型缓存），让服务器自己从镜像站下即可。
真正需要搬的只有约 47 MB：`chroma`（18.6 MB）+ `uploads`（28.5 MB）。

搬到 Docker 部署时，对应宿主机目录就是仓库下的 `./data`（已由 compose 挂载进容器）。

> 迁移前务必先停本地服务，等 30 秒再拷 —— Chroma 的段文件是异步落盘的（见 DEVLOG 两次损坏事故）。

## 五、上线后的自检清单

- [ ] `curl http://<IP>:8010/health` 返回 `index_count` 与本地一致
- [ ] 首页能打开，四个页签都渲染正常
- [ ] 溯源问答问一句能流式返回并显示证据面板
- [ ] Agent 问「我库里有哪些文献」能看到思考轨迹
- [ ] 联动阅读选中扫描件能出 55 行版面框，点一行能出译文
- [ ] 手机流量（非本机网络）也能打开，确认确实是公网可达

## 六、常见问题

| 现象 | 原因 | 处理 |
|---|---|---|
| 启动后 `/health` 报 `model_loaded:false` | 模型还在下载 / 内存不足 | 看 `docker compose logs`，或加 swap |
| 模型下载卡住 | 未走镜像站 | 确认 `HF_ENDPOINT=https://hf-mirror.com` 已生效 |
| `index_count:0` | 没搬 `data/chroma` 或目录权限不对 | 检查挂载路径与读写权限 |
| 页面打开但接口 502 | 容器内 uvicorn 未起来 | `docker compose logs api` 看 traceback |
| 公网打不开、内网正常 | 安全组未放行 8010 | 云控制台加入方向 TCP 8010 |
