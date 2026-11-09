$ErrorActionPreference = "Stop"
$project = Split-Path -Parent $PSScriptRoot
$exe = Join-Path $project ".venv\Scripts\pythonw.exe"
$script = Join-Path $PSScriptRoot "windows_wsl_proxy.py"
$listener = Get-NetTCPConnection -LocalPort 8086 -State Listen -ErrorAction SilentlyContinue
if (-not $listener) {
    if (-not (Test-Path $exe)) { throw "pythonw.exe not found: $exe" }
    if (-not (Test-Path $script)) { throw "proxy script not found: $script" }
    Start-Process -WindowStyle Hidden -FilePath $exe -ArgumentList "`"$script`"" -WorkingDirectory $project
    Write-Output "started"
} else {
    Write-Output "already-listening"
}
