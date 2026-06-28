#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_HEALTH_URL="${VITE_BACKEND_PROXY_TARGET:-http://127.0.0.1:8099}/health"

if ! curl -sf "${BACKEND_HEALTH_URL}" >/dev/null 2>&1; then
  echo "警告: 后端未就绪 (${BACKEND_HEALTH_URL})"
  echo "请先启动后端: ${ROOT}/scripts/dev-backend.sh"
  echo
fi

cd "$ROOT/frontend"
exec npm run dev
