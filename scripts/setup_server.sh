#!/usr/bin/env bash
# ScholarRAG Agent · 服务器一键部署
# 用法：sudo bash scripts/setup_server.sh
set -euo pipefail

REPO_URL="https://github.com/YankeeLio/scholar-rag-agent.git"
TARGET="/opt/scholar-rag-agent"
PORT="8010"

log() { printf '\n==> %s\n' "$1"; }

[ "$(id -u)" -eq 0 ] || { echo "请用 root 运行： sudo bash $0"; exit 1; }

log "0/7 配置 swap（4G 内存机型必需，避免加载模型时 OOM）"
MEM_MB=$(awk '/MemTotal/{print int($2/1024)}' /proc/meminfo)
if [ "$MEM_MB" -lt 6000 ] && [ ! -f /swapfile ]; then
  if ! fallocate -l 4G /swapfile 2>/dev/null; then
    dd if=/dev/zero of=/swapfile bs=1M count=4096 status=none
  fi
  chmod 600 /swapfile
  mkswap /swapfile >/dev/null
  swapon /swapfile
  grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
  echo "已启用 4G swap（物理内存 ${MEM_MB}MB）"
else
  echo "物理内存 ${MEM_MB}MB，无需额外 swap"
fi

log "1/7 检查 Docker"
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
  systemctl enable --now docker
else
  echo "已安装：$(docker --version)"
fi

log "2/7 取代码"
if [ -d "$TARGET/.git" ]; then
  git -C "$TARGET" pull --ff-only
else
  git clone --depth 1 "$REPO_URL" "$TARGET"
fi
cd "$TARGET"

log "3/7 配置密钥"
if [ ! -f apps/api/.env ]; then
  cp .env.example apps/api/.env
  printf '请粘贴 DeepSeek API Key（直接回车可跳过，稍后改 apps/api/.env）：'
  read -r KEY || true
  if [ -n "${KEY:-}" ]; then
    sed -i "s|^DEEPSEEK_API_KEY=.*|DEEPSEEK_API_KEY=$KEY|" apps/api/.env
  fi
fi
grep -E '^[A-Z_]+=' apps/api/.env || true

log "4/7 构建镜像（首次约 5-10 分钟）"
docker compose build

log "5/7 启动容器"
docker compose up -d

log "6/7 等待就绪（首次需下载约 4.3GB 模型，5-15 分钟）"
READY=0
for _ in $(seq 1 80); do
  if curl -fsS "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; then READY=1; break; fi
  printf '.'
  sleep 15
done
echo
if [ "$READY" -eq 1 ]; then
  curl -s "http://127.0.0.1:$PORT/health"; echo
else
  echo "尚未就绪，查看日志： docker compose -f $TARGET/docker-compose.yml logs --tail 80"
fi

IP=$(curl -s --max-time 5 https://api.ipify.org || echo "<公网IP>")
cat <<EOF

========================================================
  访问地址： http://$IP:$PORT
========================================================
外网打不开、本机 127.0.0.1 能打开 -> 云控制台安全组放行 TCP $PORT
首页显示 0 篇文献            -> 还没搬索引，见 docs/DEPLOY.md 第四节
EOF
