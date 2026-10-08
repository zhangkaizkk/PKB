# PKB 一键停止
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$ProjectDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectDir

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   PKB  —  停止容器" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

try {
    docker compose down 2>&1 | ForEach-Object { Write-Host "    $_" }
} catch {
    Write-Host "[X] 停止失败: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "[OK] 容器已停止" -ForegroundColor Green
