# Enterprise AI App

企业级生成式 AI 应用 Web 服务框架：基于 FastAPI、CrewAI、OceanBase 与云原生可观测性。

- **仓库**: [https://github.com/kid0317/fastapi_base](https://github.com/kid0317/fastapi_base)

## 技术栈

- **Web**: FastAPI + Uvicorn
- **AI 编排**: CrewAI（智能体/任务/流程 YAML + Python）
- **持久化**: SQLAlchemy 2.0 异步（OceanBase/MySQL 兼容）、Alembic 迁移、本地文件客户端
- **安全**: X-API-Key 鉴权、SlowAPI 限流
- **可观测**: structlog 结构化日志、Prometheus 指标、Request ID 贯穿

## 环境要求

- Python 3.11+
- 可选：Redis、MySQL/OceanBase（生产）

## 快速开始

```bash
# 克隆
git clone https://github.com/kid0317/fastapi_base.git && cd fastapi_base

# 虚拟环境与依赖
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# 配置（复制后填入阿里云 API Key 等，见下方「配置说明」）
cp .env.example .env
# 编辑 .env，至少填写 APP_LLM_API_KEY（小红书笔记等 AI 编排依赖）；
# 也可直接使用环境变量 QWEN_API_KEY（未填 APP_LLM_API_KEY 时会自动 fallback）

# 启动（任选其一，在项目根目录）
# 方式 A：虚拟环境激活后
uvicorn app.main:app --reload --app-dir src
# 方式 B：直接用 venv 的 Python（推荐，避免子进程用错解释器）
.venv/bin/python -m uvicorn app.main:app --reload --app-dir src
# 方式 C：以模块运行（需设置 PYTHONPATH）
PYTHONPATH=src python -m app
```

### 本地调试

- **命令行**（项目根目录，先激活 `.venv` 或使用 `.venv/bin/python`）：
  ```bash
  PYTHONPATH=src python -m app
  ```
  断点调试时可在 `src/app/__main__.py` 里把 `reload=True` 改为 `False`，避免 reload 子进程导致断点不命中。

- **Cursor / VS Code**：已配置 `.vscode/launch.json`，在「运行和调试」里选择：
  - **FastAPI (调试，无 reload)**：适合打断点调试，单进程。
  - **FastAPI (开发，reload)**：改代码自动重载。
  - **Python: 以模块运行 app**：以 `python -m app` 方式启动，便于在 `__main__.py` 里设断点。

### 常用端点

- 健康检查: `GET /health/live`、`GET /health/ready`
- API 文档: `GET /docs`（开发环境）
- 指标: `GET /metrics`
- **小红书爆款笔记报告**: `POST /api/v1/xhs/notes/report`，请求为 **multipart/form-data**：必填 `idea_text`（文本）、`images`（多文件）；需请求头 `X-API-Key`（开发环境可不配置 APP_API_KEYS）。返回结构化报告（当前 `data.report` 为完整报告字符串）。需配置阿里云通义 LLM（多模态与文案模型）。

## 项目结构

```
src/app/
├── main.py           # 入口、中间件、异常处理
├── api/v1/           # 版本化 API、dependencies
├── core/             # config、security
├── crews/            # agents、tasks、flows、tools、llm（CrewAI）
├── db/               # clients、models、migrations、repositories
├── schemas/          # Pydantic Request/Response/Domain
├── services/         # 领域服务
└── observability/    # 日志、指标
tests/                # unit、integration
deploy/               # docker、k8s、grafana
```

## 配置说明

复制 `.env.example` 为 `.env` 后，**至少需填入以下与阿里云、百度相关的环境变量**（其余可选）：

### 阿里云通义千问（LLM，必填以使用 AI 编排）

| 变量 | 说明 | 必填 | 获取方式 |
|------|------|------|----------|
| **APP_LLM_API_KEY**（或 **QWEN_API_KEY**） | 阿里云 DashScope API Key | **是** | [阿里云百炼 / 灵积控制台](https://dashscope.console.aliyun.com/) 创建 API-KEY |
| APP_LLM_PROVIDER | 固定填 `aliyun` | 否 | 默认 aliyun |
| APP_LLM_MODEL | 模型名，如 `qwen-plus`、`qwen-turbo` | 否 | 默认 qwen-plus |
| APP_LLM_REGION | 地域：`cn` / `intl` / `finance` | 否 | 默认 cn |
| APP_LLM_TIMEOUT | 请求超时秒数 | 否 | 默认 600 |

### 百度千帆搜索（百度搜索工具，使用搜索时必填）

| 变量 | 说明 | 必填 | 获取方式 |
|------|------|------|----------|
| **APP_BAIDU_API_KEY**（或 **BAIDU_API_KEY**） | 百度千帆 AppBuilder API Key | **使用百度搜索工具时必填** | [百度智能云千帆控制台](https://console.bce.baidu.com/qianfan/) 创建应用获取 API Key |
| APP_BAIDU_SEARCH_TIMEOUT | 搜索请求超时秒数 | 否 | 默认 30 |

### 其他常用配置

| 变量 | 说明 | 必填 |
|------|------|------|
| APP_ENV | development / staging / production | 否 |
| APP_LOG_LEVEL | DEBUG / INFO / WARNING / ERROR | 否 |
| APP_PORT | 应用服务端口（默认 8072） | 否 |
| APP_DATABASE_URL | 数据库连接串 | 生产必填 |
| APP_SECRET_KEY | 签名/会话密钥 | 生产必填 |
| APP_API_KEYS | 合法 API Key，逗号分隔 | 生产建议配置 |
| APP_XHS_MAX_IMAGES | 小红书笔记单次请求最大图片数 | 否，默认 20 |
| APP_CREW_EXECUTION_TIMEOUT | CrewAI 单阶段执行超时（秒） | 否，默认 600 |

完整项见 `.env.example`。

## 测试

```bash
# 从项目根目录执行，PYTHONPATH 已由 pyproject.toml 配置
pytest tests/ -v
```

### 小红书爆款笔记集成测试

- **Python 版（ASGITransport 进程内调用）**：

  ```bash
  pytest tests/integration/test_xhs_note.py -v
  ```

  - 使用 `tests/integration/` 目录下的 4 张测试图片：  
    `20260202161329_150_6.jpg`、`20260202161331_151_6.jpg`、`20260202161332_152_6.jpg`、`20260202161333_153_6.jpg`  
  - `idea_text` 固定为：`我想分享最近开始用地中海饮食减脂`  
  - 调用 `POST /api/v1/xhs/notes/report`，断言返回结构化报告字段齐全。

- **Shell 版（curl 调用真实服务）**：

  ```bash
  # 1. 先在一个终端启动服务（示例）
  PYTHONPATH=src python -m app

  # 2. 另一个终端执行 shell 集成测试脚本
  chmod +x tests/integration/xhs_note_curl.sh
  APP_API_KEY=your-key ./tests/integration/xhs_note_curl.sh
  ```

  - 默认请求地址：`http://127.0.0.1:8072`（与 `APP_PORT` 一致，可通过 `XHS_BASE_URL` 覆盖）  
  - Header 中携带：`X-API-Key: $APP_API_KEY`  
  - 表单字段：
    - `idea_text=我想分享最近开始用地中海饮食减脂`
    - `images=@20260202161329_150_6.jpg`（共 4 张，多次 `images` 字段上传）

## 部署

- **Docker**: `deploy/docker/Dockerfile`，多阶段构建、非 root 用户
- **K8s**: `deploy/k8s/deployment.yaml`，liveness/readiness 使用 `/health/live`、`/health/ready`
- 敏感配置使用 Secret，非敏感使用 ConfigMap，参见 `deploy/k8s/configmap.example.yaml`

## 设计文档

- 框架总体设计：见 `doc/Python AI 应用框架设计文档.md`
- 小红书爆款笔记多 Agent 项目：见 `doc/design/小红书爆款笔记项目设计文档.md`

## License

MIT
