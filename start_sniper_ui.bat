@echo off
chcp 65001 >nul
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start_windows_proxy.ps1"
if errorlevel 1 (
  echo 代理启动失败，请查看 logs\windows_wsl_proxy.log
  pause
  exit /b 1
)
powershell -NoProfile -Command "$deadline=(Get-Date).AddSeconds(20); while((Get-Date) -lt $deadline){ if (Get-NetTCPConnection -LocalPort 8086 -State Listen -ErrorAction SilentlyContinue) { exit 0 }; Start-Sleep -Milliseconds 300 }; exit 1"
if errorlevel 1 (
  echo 等待 8086 端口超时，请查看 logs\windows_wsl_proxy.log
  pause
  exit /b 1
)
start "" "http://127.0.0.1:8086"
