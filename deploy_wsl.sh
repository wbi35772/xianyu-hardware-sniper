#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

# Native Docker Engine inside WSL2: host.docker.internal must point at the
# Windows host gateway, not at the WSL Docker bridge.
HOST_GATEWAY_IP="$(ip route show default | awk '/default/ {print $3; exit}')"
if [[ -n "${HOST_GATEWAY_IP}" ]]; then
  export HOST_GATEWAY_IP
  echo "[deploy] Windows/WSL host gateway: ${HOST_GATEWAY_IP}"
else
  echo "[deploy] WARN: default gateway not found; falling back to Docker host-gateway"
fi

mkdir -p data state accounts logs images jsonl price_history prompts

echo "[deploy] building and starting containers..."
docker compose up -d --build

echo "[deploy] waiting for Web UI health..."
for _ in $(seq 1 45); do
  if curl -fsS --max-time 2 http://127.0.0.1:8086/health >/dev/null 2>&1; then
    echo "[deploy] READY: http://127.0.0.1:8086"
    echo "[deploy] login: admin / admin123"
    echo "[deploy] model input: Web UI -> 系统设置 -> AI -> 模型名称"
    exit 0
  fi
  sleep 2
done

echo "[deploy] health check timed out. Inspect logs:"
echo "  cd /mnt/d/goofish-hardware-sniper && docker compose logs --tail=120 app"
exit 1
