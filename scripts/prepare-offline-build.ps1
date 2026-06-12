# Prepare offline Docker build dependencies
# Run this script ONCE when you have good network, then build without network.
# 在有网络时运行一次，之后断网也能构建镜像。

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Preparing offline build dependencies..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# ── 1. Download pip packages ──
Write-Host "`n[1/3] Downloading pip packages..." -ForegroundColor Green
$PipDir = "$ProjectRoot\vendor\docker-build\pip"
New-Item -ItemType Directory -Force -Path $PipDir | Out-Null

cd "$ProjectRoot\apps\backend"

# Activate venv if exists
if (Test-Path ".venv\Scripts\python.exe") {
    $Python = ".venv\Scripts\python.exe"
} else {
    $Python = "python"
}

# Download all packages (including source distributions for pure-python packages like jieba)
& $Python -m pip download `
    -r requirements.txt `
    -d "$PipDir" `
    -i https://pypi.tuna.tsinghua.edu.cn/simple

$PipCount = (Get-ChildItem "$PipDir\*" -Include @("*.whl","*.tar.gz") -ErrorAction SilentlyContinue).Count
Write-Host "  Downloaded $PipCount packages to vendor/docker-build/pip/" -ForegroundColor Gray

# ── 2. Download npm packages ──
Write-Host "`n[2/3] Downloading npm packages..." -ForegroundColor Green
$NpmDir = "$ProjectRoot\vendor\docker-build\npm"
New-Item -ItemType Directory -Force -Path $NpmDir | Out-Null

cd "$ProjectRoot\apps\frontend"

# Use npm ci with custom cache to populate offline cache
$env:npm_config_cache = "$NpmDir"
npm ci --registry=https://registry.npmmirror.com

# Pack node_modules into tarball for Dockerfile extraction
if (Test-Path "node_modules") {
    $TarPath = "$NpmDir\node_modules.tar.gz"
    # Use PowerShell Compress-Archive instead of tar (Windows path compatibility)
    Compress-Archive -Path "node_modules" -DestinationPath "$NpmDir\node_modules.zip" -Force
    Write-Host "  Packed node_modules to vendor/docker-build/npm/node_modules.zip" -ForegroundColor Gray
}

# ── 3. Pull Docker base images ──
Write-Host "`n[3/3] Pulling Docker base images..." -ForegroundColor Green
$Images = @(
    "python:3.11-slim",
    "node:22-alpine",
    "nginx:alpine",
    "postgres:16-alpine",
    "redis:7-alpine"
)

foreach ($img in $Images) {
    Write-Host "  Pulling $img ..." -ForegroundColor Gray -NoNewline
    docker pull $img | Out-Null
    Write-Host " OK" -ForegroundColor Green
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Offline dependencies ready!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Next: cd docker && docker-compose up -d --build" -ForegroundColor Yellow
