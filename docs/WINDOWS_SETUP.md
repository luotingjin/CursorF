# Windows 本地安装指南

## 方式一：一键脚本（推荐）

### 步骤 1：安装 Git（若未安装）

以**管理员身份**打开 **PowerShell**，执行：

```powershell
winget install --id Git.Git -e --source winget
```

或手动下载：https://git-scm.com/download/win  
安装时勾选 **Add Git to PATH**。

### 步骤 2：克隆项目到 D:\Cursor

打开 **PowerShell** 或 **CMD**，执行：

```powershell
git clone -b cursor/tapd-testcase-generator-0f76 https://github.com/luotingjin/CursorF.git D:\Cursor
```

若目录已存在且为 Git 仓库，更新代码：

```powershell
cd D:\Cursor
git pull origin cursor/tapd-testcase-generator-0f76
```

### 步骤 3：在 Cursor 中打开

1. 打开 **Cursor**
2. **File → Open Folder** → 选择 `D:\Cursor`

### 步骤 4：安装依赖并启动

在 Cursor 终端中：

```powershell
cd D:\Cursor
pip install -r requirements.txt
copy .env.example .env
# 编辑 .env 填入 TAPD 凭证
python run_web.py
```

浏览器访问：**http://127.0.0.1:8080**

---

## 方式二：使用仓库内脚本

克隆后（或先下载脚本），在 PowerShell 中：

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
D:\Cursor\scripts\setup_windows.ps1
```

或双击 `scripts\setup_windows.bat`（建议右键以管理员身份运行）。

---

## 常见问题

| 问题 | 解决 |
|------|------|
| `git` 不是内部或外部命令 | 重装 Git 并勾选 Add to PATH，重启 Cursor |
| `D:\Cursor` 已存在 | 清空目录或换路径后再 clone |
| 克隆很慢 | 可配置 Git 代理或使用 SSH |
