@echo off
chcp 65001 >nul
echo ========================================
echo  CursorF Windows 环境初始化
echo ========================================
echo.

where git >nul 2>&1
if %errorlevel% neq 0 (
    echo [..] 未检测到 Git，尝试用 winget 安装...
    winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
    if %errorlevel% neq 0 (
        echo [!!] 自动安装失败，请手动下载安装 Git:
        echo      https://git-scm.com/download/win
        echo      安装时勾选 Add Git to PATH
        pause
        exit /b 1
    )
    echo [OK] Git 安装完成，请关闭此窗口，重新打开终端后再运行本脚本。
    pause
    exit /b 0
)

echo [OK] Git 已安装
git --version

if not exist "D:\" (
    echo [!!] D: 盘不存在，请修改脚本中的目标路径。
    pause
    exit /b 1
)

if exist "D:\Cursor\.git" (
    echo [..] 项目已存在，正在更新...
    cd /d D:\Cursor
    git fetch origin
    git checkout cursor/tapd-testcase-generator-0f76
    git pull origin cursor/tapd-testcase-generator-0f76
    goto done
)

if exist "D:\Cursor" (
    dir /a "D:\Cursor" | find " .git" >nul
    if %errorlevel% neq 0 (
        echo [!!] D:\Cursor 已存在且不是 Git 仓库，请清空后重试。
        pause
        exit /b 1
    )
)

echo [..] 正在克隆代码到 D:\Cursor ...
git clone -b cursor/tapd-testcase-generator-0f76 https://github.com/luotingjin/CursorF.git D:\Cursor
if %errorlevel% neq 0 (
    echo [!!] 克隆失败，请检查网络或 Git 配置。
    pause
    exit /b 1
)

:done
echo.
echo [OK] 代码已就绪: D:\Cursor
echo.
echo 下一步:
echo  1. Cursor 打开文件夹 D:\Cursor
echo  2. 复制 .env.example 为 .env 并填写 TAPD 凭证
echo  3. pip install -r requirements.txt
echo  4. python run_web.py
echo  5. 浏览器打开 http://127.0.0.1:8080
echo.
pause
