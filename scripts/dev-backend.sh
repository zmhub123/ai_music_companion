#!/usr/bin/env bash
# 从 backend/ 启动 API；PYTHONPATH 须包含项目根（pycore）与 backend（src）。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"
export PYTHONPATH=".:${ROOT}"

exec "${ROOT}/.venv/bin/python" -m uvicorn src.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8099}" \
  --reload \
  "$@"
