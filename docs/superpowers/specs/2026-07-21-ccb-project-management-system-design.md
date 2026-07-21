# 道一 CCB 项目管理系统 — 产品架构方案

> 撰写日期：2026-07-21
> 状态：初稿待审
> 适用对象：道一（企业微信服务商）项目管理团队

---

## 一、产品定位

以"产品模块组合驱动流程自动生成"为核心，构建面向道一项目管理的 AI 辅助系统。覆盖项目全生命周期：**售前线索 → 签约 → 执行 → 交付 → 运维**。

核心差异化价值：
1. 内置道一各产品（企微统一包/定制包、低代码平台、门户、定制化开发、运维服务）的标准部署流程知识
2. 建项目时勾选产品组合，系统自动合并生成完整项目计划（阶段、任务、里程碑、角色分工、输出物）
3. 每个任务预埋操作指引和注意事项，PM 无需翻阅历史文档
4. 右侧 AI 面板贯穿全程：问询进度、调整计划、生成文档

---

## 二、技术栈

| 层 | 技术选型 | 说明 |
|-----|--------|------|
| 前端框架 | Vue 3 + Element Plus | 本地 localhost:5173 |
| 图表渲染 | Mermaid.js | 架构图/ER图/流程图 |
| 后端框架 | Python FastAPI | 本地 API 服务 |
| 数据库 | SQLite | 本地文件数据库，无需独立服务 |
| AI 对接 | Claude Code CLI / OpenAI Codex CLI / Gemini CLI | 读取本地 API Key |
| 存储 | Git 管理 docs 目录 + 本地文件系统 | 文档/交付包统一 git 托管 |
| 部署 | 纯本地 WSL/Linux | 无需云端服务 |

---

## 三、系统架构

```
┌──────────────────────────────────────────────────────────────────┐
│                         CCB 项目管理系统                          │
├──────────────────┬───────────────────┬──────────────┬───────────┤
│   前端页面层       │   AI 面板层        │  后端引擎层   │  存储层   │
│                  │                   │              │           │
│ 项目列表/详情     │  Claude CLI 终端   │ 流程模板管理   │ SQLite DB │
│ 阶段甘特视图      │  Codex CLI 终端    │ 项目计划组装   │           │
│ 文档目录树        │  Gemini CLI 终端   │ 日期推算引擎   │ docs/目录 │
│ 交付包管理        │  对话式操作接口     │ 校验规则引擎   │           │
│ 系统配置          │  文档自动生成       │ 任务队列调度   │ 交付包归档 │
│                  │                   │              │           │
└──────────────────┴───────────────────┴──────────────┴───────────┘
```

### 布局结构

```
┌──────────────┬──────────────────────────────────┬────────────────┐
│  左侧目录树    │          中间主内容区            │   右侧AI面板    │
│              │                                  │                │
│  📁 项目总览   │  按当前视图展示：                │  ┌──────────┐ │
│  📁 项目计划   │  - 阶段列表/甘特图               │  │ 对话输入框 │ │
│  📁 交付物     │  - 文档预览(Markdown)           │  │  "项目进度"│ │
│  📁 周报       │  - 交付包管理                   │  │  "调整计划"│ │
│  📁 会议纪要   │  - 看板                         │  │  "生成文档"│ │
│  📁 归档       │                                  │  └──────────┘ │
└──────────────┴──────────────────────────────────┴────────────────┘
```

---

## 四、核心数据模型

### 4.1 产品与流程定义（预配置）

**product 产品模块表**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| name | VARCHAR(100) | 产品名：统一包企微、定制包企微、低代码平台、门户、纯定制开发、运维服务 |
| code | VARCHAR(50) | 唯一编码 |
| description | TEXT | 产品说明 |
| sort_order | INT | 排序 |

**process_template 流程模板表**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| product_id | FK | 归属产品 |
| name | VARCHAR(200) | 模板名 |
| version | VARCHAR(20) | 版本号 |
| is_active | BOOLEAN | 是否启用 |

**phase_definition 阶段定义表**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| template_id | FK | 所属模板 |
| phase_number | INT | 阶段序号 |
| name | VARCHAR(200) | 阶段名 |
| description | TEXT | 阶段目标和说明 |
| sort_order | INT | |

**task_definition 任务定义表**（关键表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| phase_id | FK | 所属阶段 |
| task_number | VARCHAR(20) | 任务编号 |
| name | VARCHAR(200) | 任务名 |
| guide | TEXT | **操作指引**——此任务具体做什么、注意事项、历史经验 |
| deliverable | TEXT | 预期输出物 |
| vendor_role | VARCHAR(100) | 我方负责角色 |
| customer_role | VARCHAR(100) | 客户方配合角色 |
| estimated_days | DECIMAL(5,1) | 标准工期(天) |
| sort_order | INT | |

### 4.2 项目运行时（动态数据）

**project 项目表**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| name | VARCHAR(200) | 项目名 |
| customer_name | VARCHAR(200) | 客户名 |
| stage | VARCHAR(20) | 阶段：presale / signed / executing / delivered / archived |
| start_date | DATE | 项目启动日期 |
| planned_end_date | DATE | 计划结束日期 |
| status | VARCHAR(20) | active / paused / completed |
| created_at | DATETIME | |

**project_product 项目产品表**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| project_id | FK | |
| product_id | FK | 客户购买的产品 |

**project_phase 项目阶段表**（由系统自动合并生成）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| project_id | FK | |
| source_phase_id | FK → phase_definition | 来源定义 |
| phase_number | INT | 合并后的阶段序号 |
| name | VARCHAR(200) | |
| planned_start | DATE | 推算后的计划开始日 |
| planned_end | DATE | 推算后的计划结束日 |
| status | VARCHAR(20) | pending / in_progress / completed / delayed |
| sort_order | INT | |

**project_task 项目任务表**（由系统自动生成，关键表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| project_phase_id | FK | |
| source_task_id | FK → task_definition | 来源任务定义 |
| task_number | VARCHAR(20) | |
| name | VARCHAR(200) | |
| guide | TEXT | 从 definition 复制过来，可调整 |
| deliverable | TEXT | |
| assignee | VARCHAR(100) | 实际指派人 |
| planned_start | DATE | |
| planned_end | DATE | |
| actual_start | DATE | |
| actual_end | DATE | |
| status | VARCHAR(20) | pending / in_progress / completed / blocked |
| progress | INT | 进度百分比 |
| notes | TEXT | PM 备注 |

### 4.3 文档与交付

**doc_asset 文档资产表**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| project_id | FK | |
| phase_id | FK | 所属阶段 |
| path | VARCHAR(500) | docs/ 目录下的相对路径 |
| title | VARCHAR(200) | 文档名 |
| doc_type | VARCHAR(50) | 会议纪要/周报/需求文档/设计文档/交付物 |
| file_type | VARCHAR(20) | md / mermaid / docx / pdf |
| generated_by | VARCHAR(20) | manual / ai |
| version | INT | |
| created_at | DATETIME | |

**delivery_package 交付包表**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| project_id | FK | |
| version | VARCHAR(20) | v1.0, v1.1... |
| status | VARCHAR(20) | drafting / reviewing / approved / archived |
| archive_path | VARCHAR(500) | 压缩包存放路径 |

---

## 五、核心业务流程

### 5.1 项目计划自动生成流程

```
[新建项目]
    │
    ├── 填写项目信息 + 选择产品组合
    │
    ├── 系统根据各产品的 process_template
    │   读取对应 phase_definition + task_definition
    │
    ├── 按以下规则合并生成 project_phase + project_task:
    │   1. 以项目启动日为 T+0
    │   2. 各阶段按定义的 sort_order 排序
    │   3. 相同或相近的阶段名自动合并（去重）
    │   4. 每个任务的计划日期 = 上级阶段开始日 + 偏移
    │
    └── 生成完成后写入 project_phase / project_task
        左侧目录树自动刷新
```

### 5.2 产品流程合并规则示例

定制包企微的阶段包含：立项 → 企微环境部署 → 业务摸底 → UAT环境 → 测试 → 试运行 → 上线
低代码平台的阶段包含：立项 → 低代码部署 → 业务摸底 → 测试 → 试运行 → 上线

合并后：
```
阶段1: 项目立项准备（取第一个出现）
阶段2: 环境搭建（企微环境部署 + 低代码部署，并行处理）
阶段3: 业务摸底与培训
阶段4: 系统集成与测试
阶段5: 试运行与投产
阶段6: 正式上线与运营
```

---

## 六、AI 面板设计

右侧 AI 面板内置三种 CLI 会话（可切换 Claude / Codex / Gemini）：

### 6.1 核心场景

| 场景 | 用户输入示例 | 系统响应 |
|------|------------|---------|
| 进度查询 | "徽商项目现在到哪了" | AI 读取项目最新 phases/tasks 状态，汇总汇报 |
| 计划调整 | "定制包企微部署延期一周，帮我重新排" | AI 调整关联 tasks 日期，检查依赖冲突，输出变更影响范围 |
| 文档生成 | "帮我生成项目启动 PPT" | AI 根据项目信息和模板，生成 Markdown 文档存入对应目录 |
| 操作指引 | "第一阶段要注意什么" | AI 查询该阶段的 task_definition.guide，汇总展示历史经验 |
| 风险检查 | "看看这个项目有什么风险" | AI 扫描逾期任务、未关闭问题、未确认项，输出风险清单 |

### 6.2 AI 操作权限

- 读取：任务列表、阶段状态、文档内容 — 允许
- 写入：调整日期、修改状态、生成文档 — 需 PM 确认后再执行
- 阻断：删除任务、修改产品组合、归档项目 — 必须由 PM 手动操作

---

## 七、项目目录结构

```
project_root/
├── docs/                          # 所有文档资产
│   ├── 01_架构设计/               # 系统架构文档
│   ├── 02_需求设计/               # 需求规格、会议纪要
│   ├── 03_开发计划/               # 项目计划、WBS
│   ├── 04_模块规格/               # 详细设计文档
│   ├── 05_经验沉淀/               # 项目经验、复盘
│   ├── 06_决策记录/               # ADR 架构决策
│   ├── 07_交付资产/               # 交付包、验收报告、架构图
│   └── 99_归档/                   # 已归档项目
│
├── backend/
│   ├── app/
│   │   ├── api/                   # FastAPI 路由
│   │   ├── models/                # SQLAlchemy 模型
│   │   ├── schemas/               # Pydantic 校验
│   │   ├── services/              # 业务逻辑（模板合并、日期推算等）
│   │   ├── core/                  # 配置、数据库连接
│   │   └── seed/                  # 初始数据（产品/流程定义）
│   ├── requirements.txt
│   └── main.py
│
├── frontend/
│   ├── src/
│   │   ├── views/                 # 页面
│   │   ├── components/            # 组件
│   │   ├── stores/                # Pinia 状态
│   │   ├── api/                   # API 调用
│   │   └── router/                # 路由
│   └── package.json
│
└── data/                          # SQLite DB 文件
```

---

## 八、业务规则

### 8.1 流程阻断规则
- 某阶段所有任务是 pending 状态，不允许进入下一阶段
- 某阶段有任务超过计划结束日 7 天未完成，自动标记风险
- 里程碑任务未完成，不允许归档项目

### 8.2 日期推算规则
- 所有日期基于项目启动日（start_date）推算
- 工作日计算（排除周末），暂不考虑法定节假日
- 任务依赖关系：前置任务未完成，后续任务不能改为 in_progress

### 8.3 交付物规则
- 每个阶段必须有对应的交付物才能标记为 completed
- 交付包导出前检查所有 required 文档是否已生成

---

## 九、推荐实现阶段

### Phase 1 — 核心引擎 MVP
- 数据模型 + 产品/流程定义种子数据
- 新建项目 + 选产品 → 自动生成项目计划
- 阶段/任务列表展示，状态更新
- SQLite 数据库落地

### Phase 2 — AI 面板接入
- 对接 Claude Code CLI
- AI 读取项目上下文对话
- 对话式计划调整
- 基础文档 AI 生成（会议纪要、周报）

### Phase 3 — 文档体系与目录
- docs 目录自动同步
- 左侧文档目录树
- Markdown 在线预览
- 交付包生成与归档

### Phase 4 — 增强功能
- 看板视图（按阶段/负责人/状态）
- 甘特图展示
- 消息通知
- 多 AI 模型切换
- 数据统计看板

---

**待补充：**
- 各产品模块的具体流程定义（phase → task 明细）——由 PM 团队梳理录入
- 售前阶段详细字段
- 交付评估审批流程细节
