# TAPD 测试用例自动生成与导入工具

自动从 TAPD 获取需求，根据需求内容生成测试用例，并批量导入回 TAPD。

## 功能特性

- 连接 TAPD Open API（支持 Basic Auth 与 Access Token）
- 按项目、迭代、状态或指定需求 ID 拉取需求
- 两种用例生成模式：
  - **rule**（默认）：基于规则解析验收标准，无需 LLM
  - **llm**：调用 OpenAI 兼容 API 智能生成
- 批量导入测试用例到 TAPD（`tcases/batch_save`）
- 可选关联测试计划（将需求与用例挂到同一测试计划）
- 导入前自动保存 JSON 预览到 `output/` 目录

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置凭证

复制配置模板：

```bash
cp .env.example .env
cp config.example.yaml config.yaml
```

在 [TAPD 开放平台](https://open.tapd.cn) 创建应用，获取 `client_id` 和 `client_secret`，并授权目标项目。

编辑 `.env`：

```env
TAPD_CLIENT_ID=你的应用ID
TAPD_CLIENT_SECRET=你的应用密钥
TAPD_WORKSPACE_ID=你的项目ID
```

### 3. 运行

```bash
# 查看符合条件的需求
python main.py list-stories

# 仅生成预览（不写入 TAPD）
python main.py generate --story-id 1010104801869398419

# 生成并导入 TAPD
python main.py run --story-id 1010104801869398419

# 批量处理（按 config.yaml 中的筛选条件）
python main.py run
```

## 配置说明

### 环境变量（`.env`）

| 变量 | 必填 | 说明 |
|------|------|------|
| `TAPD_CLIENT_ID` | 是* | 开放平台应用 ID |
| `TAPD_CLIENT_SECRET` | 是* | 开放平台应用密钥 |
| `TAPD_ACCESS_TOKEN` | 否 | 直接指定 Token（优先级更高） |
| `TAPD_WORKSPACE_ID` | 是 | TAPD 项目 ID |
| `TAPD_TEST_PLAN_ID` | 否 | 测试计划 ID（关联用例时需要） |
| `TAPD_CREATOR` | 否 | 用例创建人 |
| `OPENAI_API_KEY` | LLM 模式 | 大模型 API Key |

\* 使用 `TAPD_ACCESS_TOKEN` 时可不填 client_id/secret。

### 配置文件（`config.yaml`）

```yaml
story_filter:
  story_ids: []           # 指定需求 ID 列表
  iteration_id: null      # 按迭代筛选
  status: null            # 按状态筛选
  limit: 30
  max_pages: 10

generator:
  mode: rule              # rule | llm
  max_cases_per_story: 8

import:
  link_to_story: false    # 是否关联到测试计划
  dry_run: false
  output_dir: ./output
```

## CLI 命令

| 命令 | 说明 |
|------|------|
| `list-stories` | 列出符合条件的需求 |
| `generate` | 生成用例预览（默认 dry-run） |
| `import` | 生成并导入 TAPD |
| `run` | 完整流程 |

通用参数：

- `-c, --config`：配置文件路径（默认 `config.yaml`）
- `--story-id`：指定单个或多个需求 ID
- `--dry-run`：仅预览，不写入 TAPD

## 生成逻辑（rule 模式）

1. 解析需求 `description` 中的验收标准、列表项
2. 读取 `test_focus`（测试重点）字段
3. 自动生成：
   - 主流程验证用例
   - 各验收项对应用例
   - 异常与边界验证用例

## 关联测试计划

若需将生成的用例与需求关联到测试计划，配置：

```yaml
tapd:
  test_plan_id: "你的测试计划ID"
  creator: "your_username"

import:
  link_to_story: true
```

工具会依次调用：

- `test_plans/create_story_relation` — 关联需求
- `test_plans/create_tcase_relation` — 关联用例

## 项目结构

```
.
├── main.py                    # CLI 入口
├── config.example.yaml        # 配置模板
├── .env.example               # 环境变量模板
├── requirements.txt
└── tapd_testcase/
    ├── config.py              # 配置加载
    ├── tapd_client.py         # TAPD API 客户端
    ├── models.py              # 数据模型
    ├── pipeline.py            # 主流程
    ├── importer.py            # 用例导入
    └── generator/
        ├── rule_generator.py  # 规则生成器
        └── llm_generator.py   # LLM 生成器
```

## TAPD API 参考

- [获取需求](https://open.tapd.cn/document/api-doc/API%E6%96%87%E6%A1%A3/api_reference/story/get_stories.html)
- [批量创建测试用例](https://open.tapd.cn/document/api-doc/API%E6%96%87%E6%A1%A3/api_reference/tcase/batch_add_tcase.html)
- [client_credentials 鉴权](https://open.tapd.cn/document/api-doc/API%E6%96%87%E6%A1%A3/%E6%8E%88%E6%9D%83%E5%87%AD%E8%AF%81/%E9%A1%B9%E7%9B%AE%E6%80%81.html)

## 注意事项

1. 应用需在 TAPD 开放平台配置**测试用例**相关 API 权限
2. 目标项目需完成应用授权
3. 批量导入单次最多 200 条，工具会自动分批
4. 建议先用 `--dry-run` 或 `generate` 命令预览生成结果
