# AgentEval

一个轻量级 Agent 自动化评测与质量分析项目。内置电商数据分析 Agent **DataPilot**，通过执行轨迹同时检查回答结果、工具选择和调用顺序。

当前为 v0.1 原型，主要演示从自然语言提问、工具调用到自动评测的完整流程。

## 主要功能

- **Agent Playground**：输入问题，查看回答、结构化结果和工具调用轨迹。
- **自动评测**：内置 GMV、订单量、GMV 环比三个测试用例。
- **多维度评分**：检查结果正确性、工具选择和执行顺序，展示失败原因。
- **Badcase 演示**：提供跳过指标口径查询的版本，展示“结果正确但过程不合格”的情况。
- **模拟数据**：自动生成 600 条电商订单，无需接入真实业务数据库。

## 技术栈

- 前端：React、TypeScript、Next.js App Router，使用 vinext / Vite 运行。
- 后端：Python、FastAPI、Pydantic。
- 数据：SQLite、JSON 指标口径和测试集。
- 模型：支持 Chat Completions 工具调用的 OpenAI 兼容接口。

## 本地运行

准备 Node.js 22.13.0 或更高版本、pnpm，以及 Python 3.12。

### 1. 安装依赖

在仓库根目录执行（以下以 Windows PowerShell 为例）：

```powershell
cd agent-eval
pnpm install
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. 配置模型

```powershell
Copy-Item .env.example .env
```

编辑 `.env`，填写自己的 `DATAPILOT_API_KEY`，并根据服务商调整 `DATAPILOT_BASE_URL` 和 `DATAPILOT_MODEL`。模板中的地址和模型仅供配置参考，需确认账号支持。

`NEXT_PUBLIC_API_BASE_URL` 默认为 `http://127.0.0.1:8000`。

### 3. 启动后端

在 `agent-eval` 目录执行：

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
```

后端启动时会自动初始化演示数据库。接口文档：<http://127.0.0.1:8000/docs>。

### 4. 启动前端

另开一个终端，在 `agent-eval` 目录执行：

```powershell
pnpm dev --port 3000
```

访问 <http://localhost:3000>，在 Playground 中提问，或进入评测页面运行测试用例。

示例问题：

- 查询 2026 年 9 月 GMV
- 查询 2026 年 9 月订单量
- 查询 2026 年 9 月 GMV，并比较 8 月环比

## 项目结构

```text
AgentTrail/
├── README.md
├── AgentEval_v0.1_Design.md      # 设计文档
└── agent-eval/
    ├── app/                    # Playground、评测页面及组件
    ├── backend/
    │   ├── agents/datapilot/    # Agent、模型接口与工具
    │   ├── data/               # 数据初始化与指标口径
    │   ├── datasets/           # 基准测试用例
    │   ├── evaluators/         # 结果、工具和轨迹评测
    │   ├── schemas/            # 数据模型
    │   ├── tests/              # 后端测试
    │   └── main.py             # API 入口
    ├── .env.example            # 环境配置模板
    └── PUBLICATION_NOTES.md    # 发布注意事项
```

## 测试

在 `agent-eval` 目录执行：

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -q
```

## 使用说明

当前运行记录和评测结果保存在内存中，重启后清空。演示订单为程序生成的模拟数据，模型调用需要自行配置有效密钥，可能产生服务商费用。

请勿提交 `.env` 或真实业务数据；本地密钥、数据库、虚拟环境及构建缓存已加入 Git 忽略规则。
