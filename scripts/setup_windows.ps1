# Windows 一键安装 Git 并拉取项目到 D:\Cursor
# 用法：右键「以管理员身份运行」PowerShell，执行：
#   Set-ExecutionPolicy -Scope Process Bypass -Force; D:\setup_windows.ps1
# 或先在浏览器下载本脚本后执行。

$ErrorActionPreference = "Stop"
$TargetDir = "D:\Cursor"
$RepoUrl = "https://github.com/luotingjin/CursorF.git"
$Branch = "cursor/tapd-testcase-generator-0f76"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " CursorF 项目 Windows 环境初始化" -ForegroundColor Cyan
Write-Host " 目标目录: $TargetDir" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. 检查 / 安装 Git
function Ensure-Git {
    if (Get-Command git -ErrorAction SilentlyContinue) {
        Write-Host "[OK] Git 已安装: $(git --version)" -ForegroundColor Green
        return
    }
    Write-Host "[..] 未检测到 Git，正在尝试安装..." -ForegroundColor Yellow
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
    } else {
        Write-Host "[!!] 未找到 winget，请手动安装 Git:" -ForegroundColor Red
        Write-Host "     https://git-scm.com/download/win" -ForegroundColor Yellow
        Write-Host "     安装时勾选「Add Git to PATH」，完成后重新运行本脚本。" -ForegroundColor Yellow
        exit 1
    }
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Host "[!!] Git 安装后仍未在 PATH 中，请关闭终端重新打开后再运行。" -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] Git 安装完成: $(git --version)" -ForegroundColor Green
}

# 2. 创建目录
if (-not (Test-Path "D:\")) {
    Write-Host "[!!] D: 盘不存在，请修改脚本中的 `$TargetDir` 路径。" -ForegroundColor Red
    exit 1
}

# 3. 克隆或更新代码
function Sync-Repo {
    if (Test-Path $TargetDir) {
        $gitDir = Join-Path $TargetDir ".git"
        if (Test-Path $gitDir) {
            Write-Host "[..] 目录已存在，正在拉取最新代码..." -ForegroundColor Yellow
            Push-Location $TargetDir
            git fetch origin
            git checkout $Branch
            git pull origin $Branch
            Pop-Location
            Write-Host "[OK] 代码已更新" -ForegroundColor Green
            return
        }
        if ((Get-ChildItem $TargetDir -Force | Measure-Object).Count -gt 0) {
            Write-Host "[!!] $TargetDir 已存在且不是 Git 仓库，请清空后重试。" -ForegroundColor Red
            exit 1
        }
    } else {
        New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
    }
    Write-Host "[..] 正在克隆仓库到 $TargetDir ..." -ForegroundColor Yellow
    git clone -b $Branch $RepoUrl $TargetDir
    Write-Host "[OK] 克隆完成" -ForegroundColor Green
}

# 4. 检查 Python（可选）
function Check-Python {
    if (Get-Command python -ErrorAction SilentlyContinue) {
        Write-Host "[OK] Python: $(python --version)" -ForegroundColor Green
        Write-Host "[..] 安装 Python 依赖..." -ForegroundColor Yellow
        Push-Location $TargetDir
        python -m pip install -r requirements.txt
        Pop-Location
        Write-Host "[OK] 依赖安装完成" -ForegroundColor Green
    } else {
        Write-Host "[!!] 未检测到 Python，请安装后手动执行:" -ForegroundColor Yellow
        Write-Host "     cd D:\Cursor" -ForegroundColor Yellow
        Write-Host "     pip install -r requirements.txt" -ForegroundColor Yellow
        Write-Host "     python run_web.py" -ForegroundColor Yellow
        Write-Host "     下载: https://www.python.org/downloads/" -ForegroundColor Yellow
    }
}

Ensure-Git
Sync-Repo
Check-Python

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " 完成！下一步：" -ForegroundColor Green
Write-Host " 1. 打开 Cursor → File → Open Folder → D:\Cursor" -ForegroundColor White
Write-Host " 2. 复制 .env.example 为 .env 并填写 TAPD 凭证" -ForegroundColor White
Write-Host " 3. 终端执行: python run_web.py" -ForegroundColor White
Write-Host " 4. 浏览器打开: http://127.0.0.1:8080" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
