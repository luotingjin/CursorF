# AGENTS.md

## Cursor Cloud specific instructions

本项目是一个纯 Python CLI 工具（TAPD 测试用例自动生成与导入），无数据库、无后台服务、无 Docker，不监听任何端口。命令均为一次性执行，详见 `README.md`。

- 使用 `python3`（不是 `python`）。运行入口为 `python3 main.py <command>`，例如 `python3 main.py --help`。
- 依赖通过系统 pip 以 `--break-system-packages` 方式安装（Ubuntu 24.04 / Python 3.12 为 PEP 668 受管环境，且无 `python3-venv`）。`pytest` 不在 `requirements.txt` 中，需单独安装，启动更新脚本已包含。
- 运行测试：`python3 -m pytest tests/`（单元测试仅覆盖离线的规则生成器 `rule_generator`，无需任何凭证或网络）。
- 真实的 `list-stories` / `import` / `run` 命令需要有效的 TAPD Open API 凭证（`.env` 中的 `TAPD_WORKSPACE_ID` + `TAPD_ACCESS_TOKEN` 或 `TAPD_CLIENT_ID`/`TAPD_CLIENT_SECRET`），并会访问 `https://api.tapd.cn`。仓库不含 mock/sandbox，本环境无凭证时这些命令会因配置校验失败而报错（属预期）。
- `generator.mode: llm` 需要 `OPENAI_API_KEY`；默认 `rule` 模式完全离线、无需大模型。
- 核心的「需求 → 生成测试用例 → 保存 JSON 预览」逻辑（`tapd_testcase/generator/rule_generator.py`、`tapd_testcase/pipeline.py`、`tapd_testcase/importer.py`）可完全离线运行；预览以 dry-run 写入 `output/`（已被 `.gitignore` 忽略）。
- 注意：项目代码位于分支 `cursor/tapd-testcase-generator-0f76`，`main` 分支当前仅为占位 `README.md`。
