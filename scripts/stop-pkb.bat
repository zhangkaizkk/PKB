@echo off
chcp 65001 >nul
title PKB Stopper
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop-pkb.ps1"
echo.
pause
