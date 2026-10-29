# AgentEval v0.1 设计文档

> 项目定位：面向 Agent 的自动化评测与质量分析平台  
> 内置被测对象：DataPilot —— 电商经营数据分析 Agent  
> 当前阶段目标：先打通一条最小可运行闭环，再逐步扩展为完整评测平台

---

## 1. 项目目标

AgentEval 的核心目标不是搭建一个复杂 Agent，而是构建一套可复用的 Agent 评测体系。

当前项目由两部分组成：

- **主项目：AgentEval**
  - 测试集管理
  - 自动化评测
  - Execution Trace 分析
  - Badcase 归因
  - 回归验证
  - 数据飞轮
  - Dashboard / Report

- **内置被测对象：DataPilot**
  - 一个轻量级 Data Agent
  - 主要用于为 AgentEval 提供真实、稳定、可复现的被测对象
  - 不追求功能复杂，重点是“可测、可控、可复现、可拿到 Trace”

整体原则：

> DataPilot 负责“产生真实 Agent 行为”，AgentEval 负责“评估 Agent 行为”。

---

## 2. v0.1 总体目标

第一阶段只打通以下最小闭环：

```text
用户问题
   ↓
DataPilot
   ↓
Tool Calling
   ↓
Execution Trace
   ↓
Evaluator
   ↓
Evaluation Result
   ↓
前端展示
```

v0.1 暂不实现：

- Badcase 数据飞轮
- 完整 Dashboard
- RAG
- Browser Agent
- Multi-Agent
- MCP
- Memory
- 文件上传
- Excel 分析
- 自动报告生成
- 复杂工作流

---

## 3. DataPilot V1 定位

### 3.1 领域

DataPilot V1 定位为：

> **电商经营数据分析 Agent**

选择该领域的原因：

1. 业务背景简单，面试官容易理解
2. 数据结果可校验
3. Tool Calling 路径明确
4. 容易构造 Planning、Tool、Parameter、Hallucination 等典型 Badcase
5. 非常适合展示 Agent Evaluation 的过程评测能力

---

## 4. DataPilot V1 功能边界

### 4.1 支持指标

第一版只支持两个指标：

- GMV
- 订单量

后续版本再扩展：

- 支付用户数
- 退款率
- 客单价

### 4.2 支持问题类型

第一版只支持两类问题。

#### 类型 1：单指标查询

示例：

```text
查询 2026 年 9 月 GMV
```

#### 类型 2：简单时间对比

示例：

```text
查询 2026 年 9 月 GMV，并比较 8 月环比
```

---

## 5. DataPilot V1 Tool 设计

第一版只实现 3 个 Tool。

---

### 5.1 get_metric_definition

用途：

> 获取业务指标定义和计算口径。

Input：

```json
{
  "metric_name": "GMV"
}
```

Output：

```json
{
  "metric_name": "GMV",
  "definition": "SUM(pay_amount)",
  "filter": "pay_status = 'SUCCESS'",
  "table": "orders"
}
```

订单量示例：

```json
{
  "metric_name": "订单量",
  "definition": "COUNT(DISTINCT order_id)",
  "filter": "pay_status = 'SUCCESS'",
  "table": "orders"
}
```

---

### 5.2 get_table_schema

用途：

> 查询数据库表结构，避免 Agent 直接猜测字段。

Input：

```json
{
  "table_name": "orders"
}
```

Output：

```json
{
  "table_name": "orders",
  "columns": [
    "order_id",
    "user_id",
    "product_id",
    "pay_amount",
    "pay_status",
    "channel",
    "region",
    "pay_time"
  ]
}
```

---

### 5.3 run_sql

用途：

> 执行 Agent 自动生成的 SQL。

Input：

```json
{
  "sql": "SELECT SUM(pay_amount) AS gmv FROM orders WHERE pay_status = 'SUCCESS'"
}
```

Output：

```json
{
  "columns": [
    "gmv"
  ],
  "rows": [
    [
      120000
    ]
  ],
  "row_count": 1
}
```

---

## 6. 数据库设计

v0.1 只使用 SQLite。

数据库：

```text
ecommerce.db
```

第一版只需要一张表：

```text
orders
```

字段：

```text
order_id
user_id
product_id
pay_amount
pay_status
channel
region
pay_time
```

建议生成约 500～1000 条 Mock 数据。

### 6.1 GMV 定义

```sql
SUM(pay_amount)
WHERE pay_status = 'SUCCESS'
```

### 6.2 订单量定义

```sql
COUNT(DISTINCT order_id)
WHERE pay_status = 'SUCCESS'
```

---

## 7. Agent Run Schema

一次 DataPilot 运行必须返回统一结构。

```json
{
  "run_id": "run_20261004_001",
  "agent_name": "DataPilot",
  "agent_version": "v1.0",
  "query": "查询2026年9月GMV",
  "status": "completed",
  "trace": [],
  "final_answer": "2026年9月GMV为120000元。",
  "total_latency_ms": 1850
}
```

字段说明：

| 字段 | 含义 |
|---|---|
| run_id | 单次运行唯一 ID |
| agent_name | Agent 名称 |
| agent_version | Agent 版本 |
| query | 用户输入 |
| status | completed / failed |
| trace | 完整 Execution Trace |
| final_answer | Agent 最终答案 |
| total_latency_ms | 总耗时 |

---

## 8. Trace Schema

Trace 是整个评测平台最重要的数据底座。

以后以下模块都会依赖 Trace：

- Playground
- Evaluator
- Badcase Analysis
- Regression
- Report

单个 Trace Step 示例：

```json
{
  "step": 1,
  "type": "tool_call",
  "tool": "get_metric_definition",
  "input": {
    "metric_name": "GMV"
  },
  "output": {
    "definition": "SUM(pay_amount)",
    "filter": "pay_status = 'SUCCESS'"
  },
  "status": "success",
  "latency_ms": 23
}
```

完整示例：

```json
{
  "run_id": "run_20261004_001",
  "agent_name": "DataPilot",
  "agent_version": "v1.0",
  "query": "查询2026年9月GMV",
  "status": "completed",
  "trace": [
    {
      "step": 1,
      "type": "tool_call",
      "tool": "get_metric_definition",
      "input": {
        "metric_name": "GMV"
      },
      "output": {
        "definition": "SUM(pay_amount)",
        "filter": "pay_status = 'SUCCESS'"
      },
      "status": "success",
      "latency_ms": 23
    },
    {
      "step": 2,
      "type": "tool_call",
      "tool": "get_table_schema",
      "input": {
        "table_name": "orders"
      },
      "output": {
        "columns": [
          "order_id",
          "user_id",
          "product_id",
          "pay_amount",
          "pay_status",
          "channel",
          "region",
          "pay_time"
        ]
      },
      "status": "success",
      "latency_ms": 18
    },
    {
      "step": 3,
      "type": "tool_call",
      "tool": "run_sql",
      "input": {
        "sql": "SELECT SUM(pay_amount) AS gmv FROM orders WHERE pay_status = 'SUCCESS' AND pay_time >= '2026-09-01' AND pay_time < '2026-10-01'"
      },
      "output": {
        "columns": [
          "gmv"
        ],
        "rows": [
          [
            120000
          ]
        ],
        "row_count": 1
      },
      "status": "success",
      "latency_ms": 31
    }
  ],
  "final_answer": "2026年9月GMV为120000元。",
  "total_latency_ms": 1850
}
```

---

## 9. Case Schema

测试集中的每一条 Case 使用统一结构。

第一版示例：

```json
{
  "case_id": "case_001",
  "name": "9月GMV查询",
  "category": "metric_query",
  "query": "查询2026年9月GMV",
  "expected": {
    "result": {
      "gmv": 120000
    },
    "tools": [
      "get_metric_definition",
      "get_table_schema",
      "run_sql"
    ],
    "tool_order": [
      "get_metric_definition",
      "get_table_schema",
      "run_sql"
    ]
  },
  "tags": [
    "GMV",
    "基础能力",
    "正向Case"
  ]
}
```

v0.1 先不加入过多字段。

后续可扩展：

```text
expected_sql
expected_parameters
forbidden_tools
max_tool_calls
expected_behavior
expected_latency
```

---

## 10. Evaluation Result Schema

每一次评测输出统一格式。

```json
{
  "evaluation_id": "eval_001",
  "run_id": "run_20261004_001",
  "case_id": "case_001",
  "overall_pass": true,
  "score": 1.0,
  "dimensions": {
    "result": {
      "pass": true,
      "score": 1.0
    },
    "tool_selection": {
      "pass": true,
      "score": 1.0
    },
    "trajectory": {
      "pass": true,
      "score": 1.0
    }
  },
  "failure_types": []
}
```

失败示例：

```json
{
  "failure_types": [
    "MISSING_REQUIRED_TOOL"
  ]
}
```

---

## 11. v0.1 Evaluator 设计

第一版只实现 3 个 Evaluator。

---

### 11.1 Result Evaluator

目标：

> 判断最终结果是否正确。

第一版只校验核心数值。

示例：

```text
Expected GMV = 120000
Actual GMV = 120000

PASS
```

---

### 11.2 Tool Selection Evaluator

目标：

> 判断 Agent 是否调用了所有必须调用的 Tool。

Expected：

```text
get_metric_definition
get_table_schema
run_sql
```

Actual：

```text
get_table_schema
run_sql
```

结果：

```text
FAIL

failure_type:
MISSING_REQUIRED_TOOL
```

---

### 11.3 Trajectory Evaluator

目标：

> 判断 Tool 调用顺序是否符合预期。

Expected：

```text
get_metric_definition
→ get_table_schema
→ run_sql
```

Actual：

```text
run_sql
→ get_metric_definition
→ get_table_schema
```

结果：

```text
FAIL

failure_type:
INVALID_TOOL_ORDER
```

---

## 12. v0.1 核心演示 Case

必须准备一个经典案例：

> **最终答案正确，但过程错误。**

例如：

用户问题：

```text
查询2026年9月GMV
```

Actual Trace：

```text
get_table_schema
→ run_sql
```

最终结果：

```text
120000
```

评测结果：

```text
Result            PASS
Tool Selection    FAIL
Trajectory        FAIL
Overall           FAIL
```

这个 Case 是整个 Demo 的核心展示点之一。

它能够直接体现：

> Agent Evaluation 不只是判断最终答案，还需要评价执行过程是否正确、稳定、可复现。

---

## 13. 后端 API 设计

v0.1 使用 FastAPI。

第一版只需要 5 个 API。

---

### 13.1 POST /api/agent/run

用途：

> 单次运行 DataPilot。

Request：

```json
{
  "query": "查询2026年9月GMV",
  "agent_version": "v1.0"
}
```

Response：

返回 Agent Run Schema。

---

### 13.2 GET /api/runs/{run_id}

用途：

> 获取单次 Agent Run 和 Execution Trace。

---

### 13.3 GET /api/cases

用途：

> 获取测试集。

---

### 13.4 POST /api/evaluations/run

用途：

> 对指定 Case 执行 Agent 并完成评测。

---

### 13.5 GET /api/evaluations/{evaluation_id}

用途：

> 获取评测结果。

---

## 14. 前端 v0.1 页面设计

第一版只实现两个页面。

---

## 14.1 Agent Playground

页面采用双栏结构。

```text
┌────────────────────────┬─────────────────────────┐
│ DataPilot              │ Execution Trace         │
│ Version: v1.0          │                         │
│                        │ ① metric_definition     │
│ User                   │       ↓                 │
│ 查询9月GMV              │ ② table_schema         │
│                        │       ↓                 │
│ Agent                  │ ③ run_sql              │
│ 9月GMV为120000元        │                         │
│                        │                         │
│ [ 输入框 ]       Run   │                         │
└────────────────────────┴─────────────────────────┘
```

左侧负责展示：

- 用户 Query
- Agent Final Answer
- Agent Version
- Run

右侧负责展示：

- Tool 名称
- Tool Input
- Tool Output
- Tool 顺序
- Latency
- Success / Failed

---

## 14.2 Evaluation 页面

第一版保持极简。

```text
Case: case_001

[ Run Evaluation ]

Result            PASS
Tool Selection    PASS
Trajectory        PASS

Overall           PASS
```

---

## 15. 推荐项目目录

```text
agent-eval/
│
├── backend/
│   ├── main.py
│   │
│   ├── agents/
│   │   └── datapilot/
│   │       ├── agent.py
│   │       ├── prompts.py
│   │       └── tools.py
│   │
│   ├── evaluators/
│   │   ├── result_evaluator.py
│   │   ├── tool_evaluator.py
│   │   └── trajectory_evaluator.py
│   │
│   ├── schemas/
│   │   ├── run.py
│   │   ├── case.py
│   │   └── evaluation.py
│   │
│   ├── data/
│   │   ├── ecommerce.db
│   │   └── metrics.json
│   │
│   └── datasets/
│       └── benchmark.json
│
├── frontend/
│   └── ...
│
└── README.md
```

架构原则：

```text
Agent 执行层
Evaluator 评测层
Schema 协议层
前端展示层
```

彼此解耦。

---

## 16. v0.1 开发顺序

严格按照以下顺序开发。

### Step 0：系统架构设计

确认：

- 项目目录
- 技术栈
- 核心协议
- 模块职责

### Step 1：定义 Schema

优先完成：

1. Case Schema
2. Agent Run Schema
3. Trace Schema
4. Evaluation Result Schema

### Step 2：实现 SQLite 数据库

完成：

- orders 表
- Mock 数据
- GMV / 订单量 Ground Truth

### Step 3：实现 3 个 Tool

完成：

- get_metric_definition
- get_table_schema
- run_sql

### Step 4：实现 DataPilot V1

能力：

```text
Query
↓
LLM
↓
Tool Calling
↓
Observation
↓
Final Answer
```

核心验收点：

> 能稳定拿到结构化 Trace。

### Step 5：实现单 Case Evaluator

先支持：

- Result
- Tool Selection
- Trajectory

### Step 6：打通第一条自动评测链路

```text
Dataset
↓
Agent
↓
Trace
↓
Evaluator
↓
Evaluation Result
```

### Step 7：实现 Agent Playground

左侧：

- Chat

右侧：

- Trace

### Step 8：实现 Evaluation 页面

支持：

- 选择 Case
- Run Evaluation
- 展示 3 个维度结果

---

## 17. v0.1 验收标准

满足以下 5 条即可认为 v0.1 完成。

### 1

输入：

```text
查询 2026 年 9 月 GMV
```

DataPilot 能得到正确结果。

### 2

DataPilot 能真实调用至少 3 个 Tool：

```text
get_metric_definition
get_table_schema
run_sql
```

### 3

每一步 Tool Call 都能形成结构化 Trace。

### 4

`case_001` 可以自动完成：

- Result Evaluation
- Tool Selection Evaluation
- Trajectory Evaluation

### 5

前端能够同时展示：

```text
Agent Final Answer
+
Execution Trace
```

---

## 18. 后续版本规划

### v0.2

增加：

- Dataset Manager
- 批量 Case
- Evaluation Runner
- 批量结果

### v0.3

增加：

- Badcase Analysis
- Failure Type
- 自动归因

典型类型：

```text
Planning Error
Tool Selection Error
Tool Parameter Error
Schema Hallucination
Calculation Error
Redundant Tool Call
```

### v0.4

增加：

- Badcase 回流
- Regression Dataset
- Data Flywheel

形成：

```text
Agent
↓
Evaluation
↓
Badcase
↓
Attribution
↓
Dataset 回流
↓
Agent 优化
↓
Regression
```

### v0.5

增加：

- Agent Version Compare
- Regression
- Dashboard
- 自动化评测报告
- 可视化分析

---

## 19. 最终平台规划

后续完整 AgentEval 建议包含：

```text
Overview

Agent Playground

Dataset

Evaluation
├── Evaluation Runner
└── Evaluation Result

Badcase
├── Badcase List
└── Attribution

Regression

Report
```

模块对应的问题：

| 模块 | 解决的问题 |
|---|---|
| Agent Playground | Agent 是怎么工作的？ |
| Dataset | 我们测什么？ |
| Evaluation | 我们怎么测？ |
| Badcase | 为什么失败？ |
| Regression | 改完真的变好了吗？ |
| Report | Agent 当前整体质量怎么样？ |

---

## 20. 项目核心原则

### 原则 1

> DataPilot 不追求“强”，追求“可测”。

### 原则 2

> AgentEval 才是整个项目的核心。

### 原则 3

> 先打通一条完整链路，再扩大量 Case。

### 原则 4

> 不做纯前端假数据 Dashboard。

### 原则 5

> 所有 Evaluation 必须建立在真实 Agent Run 和真实 Trace 上。

### 原则 6

> Agent 和 Evaluation 解耦。

后续其他 Agent 只需要输出统一 Trace Schema，即可接入平台。

---

## 21. 面试时的项目定位

推荐表述：

> 我搭建了一套面向 Agent 的自动化评测与质量分析平台 AgentEval，并内置 DataPilot 作为标准化被测 Agent。平台围绕测试集、Agent 执行轨迹、多维 Evaluator、Badcase 归因和回归机制构建质量闭环，重点评估 Agent 的最终结果、工具调用和执行过程，而不仅仅关注最终回答是否正确。

后续完整版本可进一步表述：

> 通过 Badcase 自动归因和回归集回流形成持续迭代的数据飞轮，用于验证不同 Agent 版本在结果正确性、执行轨迹和工具调用质量上的变化。

---

## 22. 当前下一步

下一次正式执行时，从以下内容开始：

```text
Step 0：创建项目骨架
Step 1：定义 Pydantic Schema
Step 2：创建 SQLite + Mock 数据
Step 3：实现三个 Tool
Step 4：实现 DataPilot V1
Step 5：输出真实 Trace
```

第一目标不是“做漂亮”，而是：

> **让第一条 Case 从用户输入一直跑到 Evaluation Result。**
