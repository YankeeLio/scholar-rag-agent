# 部署说明（公网演示）

面对赛题要求的「公网在线演示地址」，本文给出最短可用路径。

## 零、先买服务器：选型与下单要点

### 必须满足的规格

| 项 | 要求 | 说明 |
|---|---|---|
| CPU | **4 核**（最低 2 核） | BGE-M3 是 CPU 推理，2 核能跑但首次索引会慢一倍 |
| 内存 | **8 GB**（最低 4 GB + swap） | 模型常驻约 2.5–3 GB，4 GB 无 swap 会 OOM |
| 磁盘 | **40 GB SSD**（最低 20 GB） | 镜像约 400 MB + 模型缓存 4.3 GB + 索引与上传件 |
| 带宽 | 3 Mbps 以上 | 只服务文字与页面图，不需要大带宽 |
| 系统镜像 | **Ubuntu 22.04 LTS** | 本文命令以此为准，Debian 12 同样可用 |
| GPU | **不需要** | 全程 CPU 推理，买 GPU 是浪费钱 |

### 三个容易买错的地方

1. **不要绑域名，直接用「公网 IP + 端口」访问**（如 `http://1.2.3.4:8010`）。
   绑域名走的是备案流程，大陆机房备案要 2–3 周，赶不上 11-18 的交稿时间；用 IP 直连**不需要备案**。
2. **买包月，至少买 3 个月**。初评截止 11-18，但评审意见要 2027 年 1 月底才出，这段时间评委随时可能点开链接。
   买「按量付费 / 1 个月」到期释放，公网地址就变成打不开的死链，属于硬伤。
3. **产品的「轻量应用服务器」比「云服务器 ECS」更划算**。4 核 8G 的轻量套餐一般在每月几十元量级，
   而 ECS 同规格更贵；两者都能跑 Docker，功能上没差别。

### 下单后要做的三件事

- 控制台 → 安全组/防火墙 → 入方向放行 **TCP 8010**（不放行则外网打不开，内网正常，最容易漏）
- 记录**公网 IP** 与登录方式（root 密码或密钥）
- 确认系统为 Ubuntu 22.04 干净镜像（不要选带面板的镜像，会额外占内存）

## 已部署实例（本仓库对应的实际运行环境）

| 项 | 值 |
|---|---|
| 访问地址 | **http://139.199.227.56:8010** |
| 规格 | 腾讯云轻量应用服务器，4 核 4 GB / 40 GB SSD / Ubuntu 22.04 |
| 部署方式 | Docker 单镜像 + `data` 目录卷挂载（未使用 compose） |
| 索引 | 921 块（教材 893 + 扫描件 28），由开发机整体迁移 |
| 低配适配 | 已启用 4 GB swap，防止 4 GB 物理内存加载 BGE-M3 时被 OOM |
| 维护 | 评分期（至 2027 年 1 月底）需保持实例与容器运行 |

> 迁移索引时有一个坑：Chroma 里 `source` 字段存的是入库机器上的绝对路径。
> 从 Windows 迁到 Linux 后该路径不存在，页面图 / 版面 / 翻译接口会返回 404。
> `main.py` 的 `_doc_source()` 已做兜底：原路径不存在时按**文件名**回退到本机 `data/uploads/` 下的同名副本。

## 一、服务器要求（速查）

| 项 | 建议 | 说明 |
|---|---|---|
| CPU | 4 核 | BGE-M3 为 CPU 推理，2 核会明显卡顿 |
| 内存 | 8 GB | 模型常驻约 2.5–3 GB，2 核 4 GB 容易 OOM |
| 磁盘 | 40 GB | 镜像约 400 MB + 模型缓存约 4.3 GB + 索引与上传件 |
| 系统 | Ubuntu 22.04 / Debian 12 | 本文命令以 Ubuntu 为例 |
| 网络 | 放行 8010 端口 | 云厂商安全组里加一条入方向规则 |

> 若只想临时演示，也可用 2 核 4 GB + 4 GB swap 顶住，但首次索引会很慢。

## 二、最快路径：一条命令（推荐）

服务器到手后，用 root 登录，直接跑仓库里的脚本，它会自动装 Docker、拉代码、配密钥、构建、启动、等就绪，最后打印访问地址：

```bash
apt update && apt install -y git
git clone --depth 1 https://github.com/YankeeLio/scholar-rag-agent.git /opt/scholar-rag-agent
sudo bash /opt/scholar-rag-agent/scripts/setup_server.sh
```

脚本会提示粘贴 DeepSeek API Key，最后输出形如：

```
========================================================
  访问地址： http://1.2.3.4:8010
========================================================
```

> 想人工控制每一步，就走下面的方式 A；想换掉 Docker，走方式 B。

## 三、方式 A：Docker（手动）

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

## 四、方式 B：不用 Docker（裸机）

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

## 五、把本地已建好的索引搬上去（省 40–70 分钟）

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

## 六、上线后的自检清单

- [ ] `curl http://<IP>:8010/health` 返回 `index_count` 与本地一致
- [ ] 首页能打开，四个页签都渲染正常
- [ ] 溯源问答问一句能流式返回并显示证据面板
- [ ] Agent 问「我库里有哪些文献」能看到思考轨迹
- [ ] 联动阅读选中扫描件能出 55 行版面框，点一行能出译文
- [ ] 手机流量（非本机网络）也能打开，确认确实是公网可达

## 七、常见问题

| 现象 | 原因 | 处理 |
|---|---|---|
| 启动后 `/health` 报 `model_loaded:false` | 模型还在下载 / 内存不足 | 看 `docker compose logs`，或加 swap |
| 模型下载卡住 | 未走镜像站 | 确认 `HF_ENDPOINT=https://hf-mirror.com` 已生效 |
| `index_count:0` | 没搬 `data/chroma` 或目录权限不对 | 检查挂载路径与读写权限 |
| 页面打开但接口 502 | 容器内 uvicorn 未起来 | `docker compose logs api` 看 traceback |
| 公网打不开、内网正常 | 安全组未放行 8010 | 云控制台加入方向 TCP 8010 |
