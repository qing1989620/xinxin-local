@echo off
chcp 65001 >nul
echo [1/2] Starting local services...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-Xinxin-Local.ps1" -NoBrowser
echo.
echo [2/2] Opening the public tunnel...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-Tunnel.ps1" %*
echo.
echo Keep this window open while you use the public address.
echo Press any key to close it (the tunnel usually keeps running).
pause >nul
