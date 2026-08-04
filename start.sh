#!/usr/bin/env bash
# =============================================================
# AI漫剧制作平台 一键启动脚本 (macOS / Linux)
# 用法: ./start.sh
#   - 自动创建 Python 虚拟环境并安装后端依赖
#   - 自动初始化 SQLite 数据库（含 10 套模板种子数据）
#   - 若 frontend/dist 已构建：仅启动后端，浏览器访问 http://localhost:8000
#   - 否则：同时启动前端开发服务器（http://localhost:5173）
# =============================================================
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "==> [1/3] 初始化后端环境"
cd "$ROOT/backend"
if [ ! -d venv ]; then
  python3 -m venv venv
fi
./venv/bin/pip install -q -r requirements.txt
./venv/bin/python init_db.py

echo "==> [2/3] 启动后端服务 (http://localhost:8000)"
./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACK_PID=$!

echo "==> [3/3] 启动前端"
if [ -d "$ROOT/frontend/dist" ]; then
  echo "    前端已构建，无需单独启动，直接访问 http://localhost:8000"
else
  cd "$ROOT/frontend"
  if [ ! -d node_modules ]; then
    npm install
  fi
  npm run dev &
  FRONT_PID=$!
  echo "    前端开发服务器: http://localhost:5173"
fi

trap 'kill $BACK_PID $FRONT_PID 2>/dev/null || true' EXIT
wait
