# 小红书爆款笔记生成 Agent 实战项目

> 课程《企业级多智能体设计实战》第 11 课《项目实战1：小红书爆款笔记生成项目》配套代码
>
> 从零搭建一个多 Agent 协作的小红书爆款笔记生成系统：用户上传图片 + 一句话意图 → 生成完整笔记报告（SEO 标题、正文、标签、图片顺序、每张图片的编辑方案）
> 如果对课程或者代码有疑问，欢迎通过我的个人微信加入微信群一起学习讨论: bmagician

## 技术栈

- **Web**: FastAPI + Uvicorn
- **AI 编排**: CrewAI（智能体/任务/流程 YAML + Python）
- **持久化**: SQLAlchemy 2.0 异步（OceanBase/MySQL 兼容）、Alembic 迁移、本地文件客户端
- **安全**: X-API-Key 鉴权、SlowAPI 限流
- **可观测**: structlog 结构化日志、Prometheus 指标、Request ID 贯穿

## 项目架构

### 核心设计

- **5 个 Agent 分工协作**：视觉分析师、图片编辑师、增长策略专家、内容撰写师、SEO 优化专家
- **7 个 Task**：视觉分析（并发）、视觉分析总结、图片编辑方案（并发）、编辑方案总结、内容策略、文案撰写、SEO 优化
- **三阶段流程编排**：阶段一视觉分析（多图并发）→ 阶段二图片编辑（多图并发）→ 阶段三内容创作（策略→文案→SEO 串行）

### Agent 角色

| Agent | 角色定位 | 模型 | 多模态 |
|-------|----------|------|--------|
| 视觉分析师 | 平台审美 + 情绪价值 + 商业转化 三重视角分析图片 | qwen3-vl-plus | 是 |
| 图片编辑师 | 轻量可复现的编辑方案，统一笔记视觉风格 | qwen3-vl-plus | 是 |
| 增长策略专家 | 制定内容策略简报，指导爆款创作 | qwen3-max | 否 |
| 内容撰写师 | 将策略转译为高情绪价值的笔记文案 | qwen3-max | 否 |
| SEO 优化专家 | 自然融入长尾关键词，优化搜索与推荐 | qwen3-max | 否 |

### 请求链路

```
POST /api/v1/xhs/notes/report
  → API 层解析 multipart 表单
  → Service 层：图片保存压缩、构建 XhsNoteIdeaRequest
  → Flow 层：三阶段 Crew 执行（visual → edit → content）
  → 汇总报告 → 返回 ApiResponse
```

### 关键文件

| 文件 | 职责 |
|------|------|
| `schemas/xhs_note.py` | 数据模型（输入/输出/领域模型） |
| `crews/config/agents.yaml` | Agent 角色配置（role/goal/backstory） |
| `crews/config/tasks.yaml` | Task 描述模板 |
| `crews/xhs_note/agents.py` | Agent 工厂函数 |
| `crews/xhs_note/tasks.py` | Task 工厂函数 |
| `crews/xhs_note/flows.py` | 三阶段流程编排 |
| `services/xhs_note_service.py` | 业务逻辑（图片压缩、调用 flow、清理临时文件） |
| `api/v1/xhs_note.py` | HTTP 端点 |

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


### 小红书笔记接口测试

在项目根目录执行（需先启动服务）：

```bash
sh tests/integration/xhs_note_curl.sh
```

### 常用端点

- 健康检查: `GET /health/live`、`GET /health/ready`
- API 文档: `GET /docs`（开发环境）
- 指标: `GET /metrics`
- **小红书爆款笔记报告**: `POST /api/v1/xhs/notes/report`  
  - 请求：**multipart/form-data**，必填 `idea_text`（创作意图）、`images`（多文件）  
  - 返回：完整报告，含 SEO 优化标题、正文、标签、图片发布顺序、每张图片的视觉分析与编辑方案  
  - 需配置阿里云通义 LLM（多模态 qwen3-vl-plus + 文案 qwen3-max）  
  - 开发环境可不配置 `X-API-Key`（未配置 APP_API_KEYS 时）

## 项目结构

```
src/app/
├── main.py              # 入口、中间件、异常处理
├── api/v1/              # 版本化 API（含 xhs_note.py）
├── core/                # config、security、image_utils
├── crews/
│   ├── config/          # agents.yaml、tasks.yaml
│   ├── xhs_note/        # agents.py、tasks.py、flows.py（小红书笔记编排）
│   ├── tools/           # AddImageToolLocal、IntermediateTool
│   └── llm/             # 阿里云通义 LLM 封装
├── schemas/             # xhs_note.py 等 Pydantic 模型
├── services/            # xhs_note_service.py
└── observability/       # 日志、指标
tests/                   # unit、integration（含 test_xhs_note.py）
doc/                     # 课程大纲、逐字稿、设计文档
deploy/                  # docker、k8s、grafana
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

## 文档与课程资料

| 文档 | 说明 |
|------|------|
| `doc/课程大纲.md` | 课程大纲（约 40 分钟，六章结构） |
| `doc/课程逐字稿.md` | 课程完整逐字稿 |
| `doc/design/小红书爆款笔记项目设计文档.md` | 项目设计文档（架构、数据模型、Agent/Task/Flow） |
| `doc/Python AI 应用框架设计文档.md` | 框架总体设计 |

**实现要点**：Agent 与 Task 均通过 **get 工厂方法**（如 `get_xhs_visual_analyst()`、`get_task_content_strategy()`）按需创建新实例，避免单例在并发下的状态共享问题。

## 课堂代码演示学习指南

### 整体架构一览

```
用户请求（图片 + 一句话意图）
         │
         ▼
    FastAPI 端点
    POST /notes/report
         │
         ▼
    xhs_note_service
    (图片上传/压缩/清理)
         │
         ▼
┌─────────────────────────────────────────┐
│  三阶段 Flow 编排（flows.py）             │
│                                         │
│  阶段1：视觉分析（并行）                   │
│  ┌──────┬──────┬──────┐                │
│  │ 图1  │ 图2  │ 图N  │ async_execution │
│  │ 视觉 │ 视觉 │ 视觉 │                 │
│  │ 分析 │ 分析 │ 分析 │                 │
│  └──┬───┴──┬───┴──┬───┘                │
│     └──────┴──────┘                     │
│            ▼                            │
│     视觉报告汇总                          │
│            │                            │
│  阶段2：修图方案（并行）                   │
│  ┌──────┬──────┬──────┐                │
│  │ 图1  │ 图2  │ 图N  │ async_execution │
│  │ 修图 │ 修图 │ 修图 │                 │
│  └──┬───┴──┬───┴──┬───┘                │
│     └──────┴──────┘                     │
│            ▼                            │
│     修图方案汇总                          │
│            │                            │
│  阶段3：内容创作（串行）                   │
│  策略 ──→ 文案 ──→ SEO                  │
│  context    context                     │
└─────────────────────────────────────────┘
         │
         ▼
    XhsNoteReportResponse（最终报告）
```

### 学习路线

---

#### 第一步：看数据模型（契约先行）

**阅读文件**：`src/app/schemas/xhs_note.py`

| 模型 | 阶段 | 作用 |
|------|------|------|
| `XhsImageVisualAnalysis` | 阶段1 | 单张图片视觉分析结果 |
| `XhsVisualBatchReport` | 阶段1 | N 张图的汇总报告 |
| `XhsImageEditPlan` | 阶段2 | 单张图的修图方案 |
| `XhsImageEditBatchReport` | 阶段2 | N 张图的修图汇总 |
| `XhsContentStrategyBrief` | 阶段3 | 内容策略 |
| `XhsCopywritingOutput` | 阶段3 | 文案产出 |
| `XhsSEOOptimizedNote` | 阶段3 | SEO 优化后的最终笔记 |
| `XhsNoteReportResponse` | 最终 | 完整报告（含所有阶段结果） |

**理解要点**：13 个 Pydantic 模型是在写任何 Agent/Task 代码之前就定义好的。这是"契约先行"——先定义数据接口，再实现业务逻辑。每个 Agent 的输入输出都通过 Pydantic 模型严格约束。

---

#### 第二步：看五个 Agent 的角色设计

**阅读文件**：`src/app/crews/xhs_note/agents.py` + `config/agents.yaml`

| Agent | 角色 | 多模态 | 核心能力 |
|-------|------|--------|---------|
| 视觉分析师 | 资深 MCN 视觉分析师 | ✅ qwen3-vl-plus | 图片内容/氛围/质量分析 |
| 修图策划师 | 资深修图策划师 | ✅ qwen3-vl-plus | 修图方案（滤镜/裁切/文字） |
| 策略专家 | 增长策略专家 | ❌ | CES 评分/反漏斗/语义工程 |
| 文案编辑 | 爆款文案编辑 | ❌ | 标题/正文/互动引导 |
| SEO 优化师 | SEO 优化师 | ❌ | 标签/关键词/发布建议 |

**理解要点**：
- 每个 Agent 的 backstory 遵循四段式结构：身份背景 → 核心知识/理论 → 工作方法/习惯 → 行为边界
- Agent 工厂函数每次调用都创建新实例（`get_xhs_visual_analyst()` 而不是全局单例）——防止并发请求间的状态污染

---

#### 第三步：看七个 Task 的模板设计

**阅读文件**：`src/app/crews/xhs_note/tasks.py` + `config/tasks.yaml`

| Task | 对应 Agent | 输出模型 | async |
|------|-----------|---------|-------|
| 单图视觉分析 | 视觉分析师 | `XhsImageVisualAnalysis` | ✅ |
| 视觉报告汇总 | 视觉分析师 | `XhsVisualBatchReport` | ❌ |
| 单图修图方案 | 修图策划师 | `XhsImageEditPlan` | ✅ |
| 修图方案汇总 | 修图策划师 | `XhsImageEditBatchReport` | ❌ |
| 内容策略 | 策略专家 | `XhsContentStrategyBrief` | ❌ |
| 文案撰写 | 文案编辑 | `XhsCopywritingOutput` | ❌ |
| SEO 优化 | SEO 优化师 | `XhsSEOOptimizedNote` | ❌ |

**理解要点**：
- Task 描述在 YAML 中使用模板变量（`{idea_text}`、`{images_info}`），运行时通过 `kickoff(inputs={...})` 注入
- `async_execution=True` 的 Task 在同一个 Crew 内并行执行（同一阶段的 N 张图同时分析）

---

#### 第四步：看三阶段 Flow 编排

**阅读文件**：`src/app/crews/xhs_note/flows.py`

| 阶段 | Crew 内并行？ | 阶段间关系 |
|------|-------------|-----------|
| 阶段1 视觉分析 | ✅ N 个分析 Task 并行 + 1 个汇总 | 独立启动 |
| 阶段2 修图方案 | ✅ N 个方案 Task 并行 + 1 个汇总 | 依赖阶段1 |
| 阶段3 内容创作 | ❌ 3 个 Task 严格串行 | 依赖阶段1+2 |

**理解要点**：
- 每个阶段创建独立的 Crew 实例（工厂模式）
- 阶段间串行（阶段2 需要阶段1 的结果），阶段内可并行
- `asyncio.wait_for()` 为每个阶段设置超时，防止 LLM 调用无限等待

---

#### 第五步：看 YAML+Python 分离模式

**阅读文件**：对比 `config/agents.yaml` 和 `agents.py`

| 放在 YAML 中 | 放在 Python 中 |
|-------------|---------------|
| role / goal / backstory（文案内容） | LLM 绑定、tools 绑定 |
| description / expected_output（任务描述） | output_pydantic、async_execution |
| 模板变量 `{idea_text}` | 变量注入逻辑 |

**理解要点**：分离的原则是"文案 vs 结构"——需要频繁调整的文案内容放 YAML（产品经理也能改），代码结构放 Python。

---

#### 第六步：看企业级工程实践

**阅读文件**：`src/app/` 各模块

| 模块 | 文件 | 工程实践 |
|------|------|---------|
| 安全 | `core/security.py` | API Key 认证（生产环境强制） |
| 可观测性 | `observability/` | structlog + Prometheus + W3C Trace |
| 图片处理 | `core/image_utils.py` | Pillow 压缩 → 降低多模态 token 消耗 |
| 数据层 | `db/` | SQLAlchemy 2.0 异步 + Alembic 迁移 |
| 部署 | `deploy/` | 多阶段 Dockerfile + K8s 3 副本 |

---

#### 第七步：运行测试

```bash
python3 -m pytest tests/ -v
```

---

### 学习检查清单

- [ ] "数据模型先行"解决了什么问题？（先定义 Agent 间的数据接口，再实现逻辑——确保各 Agent 产出严格对齐）
- [ ] 为什么 Agent 工厂函数每次创建新实例？（防止并发请求间的状态污染——CrewAI 内部有运行时状态）
- [ ] 三阶段 Flow 编排中，哪些 Task 可以并行？（阶段1 和阶段2 的 N 个图片分析/修图 Task 可以并行）
- [ ] YAML 和 Python 分别放什么？（YAML 放文案内容，Python 放结构绑定——分离关注点）
- [ ] `async_execution=True` 在哪个层面并行？（同一个 Crew 内的 Task 并行，不是跨 Crew 并行）
- [ ] backstory 的四段式结构是什么？（身份背景 → 核心知识 → 工作方法 → 行为边界）

---

## License

MIT
