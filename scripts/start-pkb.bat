@echo off
chcp 65001 >nul
title PKB Launcher
REM PKB launcher - calls PowerShell main script
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-pkb.ps1"
echo.
pause
