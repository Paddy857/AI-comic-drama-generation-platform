@echo off
REM =============================================================
REM AI漫剧制作平台 一键启动脚本 (Windows)
REM 用法: start.bat
REM   - 自动创建 Python 虚拟环境并安装后端依赖
REM   - 自动初始化 SQLite 数据库（含 10 套模板种子数据）
REM   - 若 frontend\dist 已构建：仅启动后端，浏览器访问 http://localhost:8000
REM   - 否则：同时启动前端开发服务器（http://localhost:5173）
REM =============================================================
cd /d %~dp0

echo ==^> [1/3] 初始化后端环境
cd backend
if not exist .env (
  copy .env.example .env >nul
  echo     已从 .env.example 生成 .env
)
if not exist venv (
  python -m venv venv
)
venv\Scripts\pip install -q -r requirements.txt
venv\Scripts\python init_db.py

echo ==^> [2/3] 启动后端服务 ^(http://localhost:8000^)
start "AI漫剧平台-后端" cmd /k venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000

echo ==^> [3/3] 启动前端
cd ..
if exist frontend\dist (
  echo     前端已构建，无需单独启动，直接访问 http://localhost:8000
) else (
  cd frontend
  if not exist node_modules (
    call npm install
  )
  start "AI漫剧平台-前端" cmd /k npm run dev
  echo     前端开发服务器: http://localhost:5173
)

echo.
echo 启动完成！浏览器访问 http://localhost:8000
pause
