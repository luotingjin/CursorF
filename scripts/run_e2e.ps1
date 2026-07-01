# 安装依赖并运行 Playwright E2E 测试
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$Python = "C:\Users\luotingjin\AppData\Local\Programs\Python\Python312\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

Write-Host "安装开发依赖..."
& $Python -m pip install -r requirements-dev.txt -q

Write-Host "运行 E2E 测试（使用本机 Chrome）..."
& $Python -m pytest tests/e2e -v --browser chromium
