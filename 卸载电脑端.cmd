@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0desktop\Uninstall-Xinxin-Desktop.ps1" %*
if errorlevel 1 pause
