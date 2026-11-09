@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo [start] Docker in WSL2: goofish-hardware-sniper
wsl.exe -e bash -lc "cd /mnt/d/goofish-hardware-sniper && sed -i 's/\r$//' deploy_wsl.sh && chmod +x deploy_wsl.sh && ./deploy_wsl.sh"
if errorlevel 1 (
  echo [start] WSL deploy failed
  pause
  exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start_windows_proxy.ps1"
powershell -NoProfile -Command "$deadline=(Get-Date).AddSeconds(20); while((Get-Date) -lt $deadline){ if (Get-NetTCPConnection -LocalPort 8086 -State Listen -ErrorAction SilentlyContinue) { exit 0 }; Start-Sleep -Milliseconds 300 }; exit 1"
if errorlevel 1 (
  echo [start] localhost proxy failed; check logs\windows_wsl_proxy.log
  pause
  exit /b 1
)
echo [start] READY: http://127.0.0.1:8086
pause
