# PKB 一键启动 — PowerShell 主脚本
$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# ========== 1. 定位项目根目录 ==========
$ProjectDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectDir
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   PKB  个人知识库  —  一键启动" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "项目: $ProjectDir"

# ========== 2. Docker Desktop ==========
Write-Host ""
Write-Host "[*] 检查 Docker ..." -ForegroundColor Yellow

$dockerOk = $false
try { docker info *> $null; $dockerOk = $true } catch {}

if (-not $dockerOk) {
    Write-Host "    Docker 未运行，正在启动 Docker Desktop ..."
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    Write-Host "    等待就绪（最长 3 分钟）..." -ForegroundColor DarkGray

    $wait = 0
    while ($wait -lt 36) {
        Start-Sleep -Seconds 5
        $wait++
        try { docker info *> $null; $dockerOk = $true; break } catch {}
    }
}

if (-not $dockerOk) {
    Write-Host "[X] Docker 启动超时，请手动打开 Docker Desktop 后重试" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}
Write-Host "[OK] Docker 已就绪" -ForegroundColor Green

# ========== 3. 判断是否需要 build ==========
# 场景 A: 用户传了 -rebuild 或命令行有 "rebuild"
# 场景 B: backend / frontend 镜像都不存在（首次启动）
# 场景 C: frontend/dist 时间戳比镜像新（前端改了没 build）
$needBuild = $false
$forceBuild = $false
$argsRaw = ($args -join " ").ToLower()
if ($argsRaw -match "rebuild|force") { $forceBuild = $true; $needBuild = $true }

# 检测镜像是否存在
$backendImg = docker images --format "{{.Repository}}:{{.Tag}}" 2>$null | Select-String "^pkb-backend:"
$frontendImg = docker images --format "{{.Repository}}:{{.Tag}}" 2>$null | Select-String "^pkb-frontend:"

if (-not $backendImg -or -not $frontendImg) {
    Write-Host "[*] 检测到镜像缺失，需要首次构建" -ForegroundColor Yellow
    $needBuild = $true
}

# 检测 frontend 源文件是否比镜像新
$frontDir = Join-Path $ProjectDir "frontend"
$distDir  = Join-Path $frontDir "dist"
if ((Test-Path (Join-Path $frontDir "package.json")) -and (Test-Path $distDir)) {
    # 取 dist 里最新文件的 mtime
    $distNewest = (Get-ChildItem $distDir -Recurse -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1).LastWriteTime
    # 取 src 里最新的源文件
    $srcNewest = (Get-ChildItem (Join-Path $frontDir "src") -Recurse -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1).LastWriteTime

    if ($srcNewest -gt $distNewest) {
        Write-Host "[*] 检测到前端源码有更新（src > dist），需要重新编译" -ForegroundColor Yellow
        $needBuild = $true
    }
}

# ========== 4. 前端 host build（仅在需要时）==========
if ($needBuild -and (Test-Path (Join-Path $frontDir "package.json"))) {
    Write-Host ""
    Write-Host "[1/3] 编译前端 (npm run build) ..." -ForegroundColor Yellow
    Push-Location $frontDir
    npm run build
    $npmExit = $LASTEXITCODE
    Pop-Location

    if ($npmExit -ne 0) {
        Write-Host "[X] 前端编译失败 (exit=$npmExit)，继续用现有 dist 启动..." -ForegroundColor Red
    } else {
        Write-Host "[OK] 前端编译完成" -ForegroundColor Green
    }
} else {
    Write-Host "[1/3] 前端无需重新编译" -ForegroundColor DarkGray
}

# ========== 5. Docker Compose ==========
Write-Host ""
Write-Host "[2/3] 启动容器 ..." -ForegroundColor Yellow

if ($needBuild) {
    Write-Host "    (需要构建镜像，首次启动或有代码变更)" -ForegroundColor DarkGray
    Push-Location $ProjectDir
    docker compose up -d --build
    $composeExit = $LASTEXITCODE
    Pop-Location
} else {
    Write-Host "    (镜像已存在，跳过构建)" -ForegroundColor DarkGray
    Push-Location $ProjectDir
    docker compose up -d
    $composeExit = $LASTEXITCODE
    Pop-Location
}

if ($composeExit -ne 0) {
    Write-Host "[X] Docker Compose 启动失败 (exit=$composeExit)" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}
Write-Host "[OK] 容器已启动" -ForegroundColor Green

# ========== 6. 等待后端健康 ==========
Write-Host ""
Write-Host "[3/3] 等待后端就绪 ..." -ForegroundColor Yellow
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 2
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:8000/docs" -UseBasicParsing -TimeoutSec 3
        if ($resp.StatusCode -eq 200) { $ready = $true; break }
    } catch {}
    Write-Host "    ... 等待中 ($(($i+1)*2)s / 60s)" -ForegroundColor DarkGray
}

if (-not $ready) {
    Write-Host "[X] 后端启动超时，日志如下：" -ForegroundColor Red
    docker compose logs --tail=30 backend 2>&1
    Read-Host "按回车键退出"
    exit 1
}

# ========== 7. 完成 ==========
Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "       OK 启动完成！" -ForegroundColor Green
Write-Host ""
Write-Host "   前端: http://localhost:8080" -ForegroundColor White
Write-Host "   后端: http://localhost:8000/docs" -ForegroundColor White
Write-Host "   账号: admin   密码: admin123" -ForegroundColor White
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

Start-Process "http://localhost:8080"
exit 0
