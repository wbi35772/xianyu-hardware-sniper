@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo   闲鱼 DIY 硬件狙击系统 - 本地一键启动
echo   项目目录: %CD%
echo ============================================================

set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "RUNNING_IN_DOCKER=false"
set "SERVER_PORT=8086"
set "OPENAI_BASE_URL=http://127.0.0.1:8088/v1"

where python >nul 2>nul
if errorlevel 1 (
  echo [错误] 未找到 Python，请先安装 Python 3.10+ 并加入 PATH。
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo [1/5] 创建 Python 虚拟环境 .venv ...
  python -m venv .venv
  if errorlevel 1 (
    echo [错误] 创建虚拟环境失败。
    pause
    exit /b 1
  )
) else (
  echo [1/5] 已存在虚拟环境 .venv
)

call ".venv\Scripts\activate.bat"

echo [2/5] 安装/更新 Python 依赖 ...
python -m pip install --upgrade pip -q
python -m pip install -r requirements.txt -q
if errorlevel 1 (
  echo [错误] Python 依赖安装失败，请检查网络或 Python 版本。
  pause
  exit /b 1
)

echo [3/5] 检查 Playwright Chromium ...
python -c "from playwright.sync_api import sync_playwright; p=sync_playwright().start(); b=p.chromium.launch(headless=True); b.close(); p.stop()" >nul 2>nul
if errorlevel 1 (
  echo       未检测到可用 Chromium，开始下载（约 150MB，仅首次）...
  python -m playwright install chromium
  if errorlevel 1 (
    echo [警告] Chromium 下载失败。Web 面板仍可启动，但监控任务无法运行。
    echo         可稍后手动执行: python -m playwright install chromium
  )
)

echo [4/5] 构建 Web UI ...
where npm >nul 2>nul
if errorlevel 1 (
  echo [错误] 未找到 npm，请安装 Node.js 20+。
  pause
  exit /b 1
)
if not exist "web-ui\node_modules" (
  echo       首次安装前端依赖 ...
  pushd web-ui
  call npm install
  if errorlevel 1 (
    popd
    echo [错误] npm install 失败。
    pause
    exit /b 1
  )
  popd
)
pushd web-ui
call npm run build
if errorlevel 1 (
  popd
  echo [错误] 前端构建失败。
  pause
  exit /b 1
)
popd
if not exist "dist\index.html" (
  echo [错误] 前端构建产物 dist\index.html 不存在。
  pause
  exit /b 1
)

echo [5/5] 探测本地 LLM 8088 ...
python -c "import json,urllib.request; u='http://127.0.0.1:8088/v1/models'; d=json.load(urllib.request.urlopen(u,timeout=3)); ids=[m.get('id') for m in d.get('data',[])]; print('       在线模型:', ', '.join([i for i in ids if i]) or '(空)')" 2>nul
if errorlevel 1 (
  echo       [警告] 127.0.0.1:8088 未就绪，先启动本地 LLM 再跑监控任务。
  echo       当前 OPENAI_MODEL_NAME=default，若服务模型名不同请在 .env 修改。
)

echo ============================================================
echo   Web 管理面板: http://127.0.0.1:8086
echo   默认账号: admin / admin123
echo   健康检查:   http://127.0.0.1:8086/health
echo   按 Ctrl+C 停止服务
echo ============================================================
python -m src.app

echo.
echo 服务已退出。
pause
