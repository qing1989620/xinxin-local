@echo off
chcp 65001 >nul
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Setup-Lan-Access.ps1" %*
if errorlevel 1 pause
