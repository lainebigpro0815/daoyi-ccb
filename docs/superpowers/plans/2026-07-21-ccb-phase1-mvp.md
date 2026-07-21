# CCB 项目管理系统 — Phase 1 MVP 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 核心流程引擎 MVP — 新建项目、选择产品组合、自动合并生成项目计划、阶段/任务列表展示与状态更新

**Architecture:** 后端 Python FastAPI + SQLAlchemy + SQLite，前端 Vue3 + Element Plus + Vite。后端 RESTful API 无状态设计，前端单页应用通过 API 通信。计划合并引擎在 services 层实现，纯函数式无副作用方便测试。

**Tech Stack:**
- 后端：Python 3.11+, FastAPI, SQLAlchemy 2.0, Alembic (可选), SQLite
- 前端：Vue 3 (Composition API), Element Plus, Pinia, Axios, Vite
- 工具：pip, Node.js 20+, pnpm (或 npm)

## Global Constraints

- 纯本地部署，SQLite 文件数据库
- 所有 API 返回 JSON 格式，统一错误响应
- 前端使用 Element Plus 组件库，中文语言包
- 日期字段统一为 ISO 格式 (YYYY-MM-DD)
- 后端端口 8000，前端端口 5173，Vite proxy 跨域

---

## 文件结构

```
D:\APM\
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── product.py          # Product
│   │   │   ├── template.py         # ProcessTemplate, PhaseDefinition, TaskDefinition
│   │   │   └── project.py          # Project, ProjectProduct, ProjectPhase, ProjectTask
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── product.py
│   │   │   ├── template.py
│   │   │   └── project.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── products.py
│   │   │   ├── templates.py
│   │   │   └── projects.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── plan_generator.py
│   │   └── seed.py                 # 种子数据（所有产品/模板/阶段/任务定义）
│   └── tests/
│       ├── __init__.py
│       ├── test_plan_generator.py
│       └── conftest.py
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── index.html
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   ├── env.d.ts
│   └── src/
│       ├── main.ts
│       ├── App.vue
│       ├── style.css
│       ├── router/
│       │   └── index.ts
│       ├── api/
│       │   ├── index.ts
│       │   ├── products.ts
│       │   ├── projects.ts
│       │   └── tasks.ts
│       ├── views/
│       │   ├── ProjectList.vue
│       │   ├── ProjectNew.vue
│       │   └── ProjectDetail.vue
│       ├── components/
│       │   ├── PhaseCard.vue
│       │   └── TaskItem.vue
│       └── stores/
│           └── project.ts
└── data/                           # SQLite 数据库文件目录
```

---

### Task 1: 后端脚手架 — FastAPI + SQLAlchemy + SQLite

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/main.py`
- Create: `backend/app/__init__.py`
- Create: `backend/app/database.py`
- Create: `backend/app/models/__init__.py`

**Interfaces:**
- Produces: `main.py` 含 FastAPI app 实例、CORS 配置、启动声明
- Produces: `database.py` 含 `engine`、`SessionLocal`、`Base`、`get_db()` 依赖注入函数

- [ ] **Step 1: Create requirements.txt**

```txt
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy==2.0.35
pydantic==2.9.0
pydantic-settings==2.5.0
```

- [ ] **Step 2: Create database.py**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./data/ccb.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 3: Create main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base

app = FastAPI(title="CCB 项目管理系统 API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/api/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 4: Create models/__init__.py**

```python
from app.database import Base
from app.models.product import Product
from app.models.template import ProcessTemplate, PhaseDefinition, TaskDefinition
from app.models.project import Project, ProjectProduct, ProjectPhase, ProjectTask
```

- [ ] **Step 5: Test scaffolding works**

```bash
cd D:\APM\backend
mkdir -p app/models app/schemas app/api app/services data
pip install -r requirements.txt
python -c "
from app.database import engine, Base
# Verify imports work
from app.models.product import Product
print('Scaffolding OK')
"
```

Expected: `Scaffolding OK`

- [ ] **Step 6: Start server to verify**

```bash
cd D:\APM\backend
uvicorn main:app --reload --port 8000
```

Then in another terminal:
```bash
curl http://localhost:8000/api/health
```

Expected: `{"status":"ok"}`
Stop the server after verification.

---

### Task 2: 数据模型 — Product + ProcessTemplate + PhaseDefinition + TaskDefinition

**Files:**
- Create: `backend/app/models/product.py`
- Create: `backend/app/models/template.py`
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/product.py`
- Create: `backend/app/schemas/template.py`

**Interfaces:**
- Consumes: `Base` from `app.database`
- Produces: Product, ProcessTemplate, PhaseDefinition, TaskDefinition SQLAlchemy models
- Produces: Pydantic schemas for each model (read, list)

- [ ] **Step 1: Create models/product.py**

```python
from sqlalchemy import Column, Integer, String, Text, Boolean
from app.database import Base


class Product(Base):
    __tablename__ = "product"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="产品名")
    code = Column(String(50), unique=True, nullable=False, comment="唯一编码")
    description = Column(Text, default="", comment="产品说明")
    sort_order = Column(Integer, default=0, comment="排序")
    is_active = Column(Boolean, default=True, comment="是否启用")
```

- [ ] **Step 2: Create models/template.py**

```python
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from app.database import Base


class ProcessTemplate(Base):
    __tablename__ = "process_template"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("product.id"), nullable=False)
    name = Column(String(200), nullable=False)
    version = Column(String(20), default="1.0")
    is_active = Column(Boolean, default=True)

    phases = relationship("PhaseDefinition", back_populates="template",
                          order_by="PhaseDefinition.sort_order")


class PhaseDefinition(Base):
    __tablename__ = "phase_definition"

    id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(Integer, ForeignKey("process_template.id"), nullable=False)
    phase_number = Column(Integer, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    sort_order = Column(Integer, default=0)

    template = relationship("ProcessTemplate", back_populates="phases")
    tasks = relationship("TaskDefinition", back_populates="phase",
                         order_by="TaskDefinition.sort_order")


class TaskDefinition(Base):
    __tablename__ = "task_definition"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phase_id = Column(Integer, ForeignKey("phase_definition.id"), nullable=False)
    task_number = Column(String(20), default="")
    name = Column(String(200), nullable=False)
    guide = Column(Text, default="", comment="操作指引/注意事项")
    deliverable = Column(Text, default="", comment="预期输出物")
    vendor_role = Column(String(100), default="", comment="我方负责角色")
    customer_role = Column(String(100), default="", comment="客户方配合角色")
    estimated_days = Column(DECIMAL(5, 1), default=1.0, comment="标准工期(天)")
    sort_order = Column(Integer, default=0)

    phase = relationship("PhaseDefinition", back_populates="tasks")
```

- [ ] **Step 3: Create models/project.py**

```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from app.database import Base


class Project(Base):
    __tablename__ = "project"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    customer_name = Column(String(200), default="")
    stage = Column(String(20), default="presale",
                   comment="presale/signed/executing/delivered/archived")
    start_date = Column(Date, nullable=False)
    planned_end_date = Column(Date, nullable=True)
    status = Column(String(20), default="active", comment="active/paused/completed")
    created_at = Column(DateTime, default=datetime.now)

    products = relationship("ProjectProduct", back_populates="project")
    phases = relationship("ProjectPhase", back_populates="project",
                          order_by="ProjectPhase.sort_order")


class ProjectProduct(Base):
    __tablename__ = "project_product"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("project.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("product.id"), nullable=False)

    project = relationship("Project", back_populates="products")
    product = relationship("Product")


class ProjectPhase(Base):
    __tablename__ = "project_phase"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("project.id"), nullable=False)
    source_phase_id = Column(Integer, ForeignKey("phase_definition.id"), nullable=True)
    phase_number = Column(Integer, nullable=False)
    name = Column(String(200), nullable=False)
    planned_start = Column(Date, nullable=True)
    planned_end = Column(Date, nullable=True)
    status = Column(String(20), default="pending",
                    comment="pending/in_progress/completed/delayed")
    sort_order = Column(Integer, default=0)

    project = relationship("Project", back_populates="phases")
    tasks = relationship("ProjectTask", back_populates="phase",
                         order_by="ProjectTask.sort_order")


class ProjectTask(Base):
    __tablename__ = "project_task"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_phase_id = Column(Integer, ForeignKey("project_phase.id"), nullable=False)
    source_task_id = Column(Integer, ForeignKey("task_definition.id"), nullable=True)
    task_number = Column(String(20), default="")
    name = Column(String(200), nullable=False)
    guide = Column(Text, default="")
    deliverable = Column(Text, default="")
    assignee = Column(String(100), default="")
    planned_start = Column(Date, nullable=True)
    planned_end = Column(Date, nullable=True)
    actual_start = Column(Date, nullable=True)
    actual_end = Column(Date, nullable=True)
    status = Column(String(20), default="pending",
                    comment="pending/in_progress/completed/blocked")
    progress = Column(Integer, default=0, comment="进度0-100")
    notes = Column(Text, default="")
    sort_order = Column(Integer, default=0)

    phase = relationship("ProjectPhase", back_populates="tasks")
```

- [ ] **Step 4: Create Pydantic schemas**

`backend/app/schemas/product.py`:
```python
from pydantic import BaseModel
from typing import Optional


class ProductBase(BaseModel):
    name: str
    code: str
    description: str = ""
    sort_order: int = 0


class ProductResponse(ProductBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True


class ProductList(BaseModel):
    items: list[ProductResponse]
```

`backend/app/schemas/template.py`:
```python
from pydantic import BaseModel
from typing import Optional


class TaskDefinitionResponse(BaseModel):
    id: int
    task_number: str
    name: str
    guide: str
    deliverable: str
    vendor_role: str
    customer_role: str
    estimated_days: float
    sort_order: int

    class Config:
        from_attributes = True


class PhaseDefinitionResponse(BaseModel):
    id: int
    phase_number: int
    name: str
    description: str
    sort_order: int
    tasks: list[TaskDefinitionResponse] = []

    class Config:
        from_attributes = True


class ProcessTemplateResponse(BaseModel):
    id: int
    product_id: int
    name: str
    version: str
    is_active: bool
    phases: list[PhaseDefinitionResponse] = []

    class Config:
        from_attributes = True
```

`backend/app/schemas/project.py`:
```python
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class ProjectProductResponse(BaseModel):
    product_id: int

    class Config:
        from_attributes = True


class ProjectTaskResponse(BaseModel):
    id: int
    project_phase_id: int
    task_number: str
    name: str
    guide: str
    deliverable: str
    assignee: str
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    status: str = "pending"
    progress: int = 0
    notes: str = ""
    sort_order: int = 0

    class Config:
        from_attributes = True


class ProjectPhaseResponse(BaseModel):
    id: int
    phase_number: int
    name: str
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    status: str = "pending"
    sort_order: int = 0
    tasks: list[ProjectTaskResponse] = []

    class Config:
        from_attributes = True


class ProjectResponse(BaseModel):
    id: int
    name: str
    customer_name: str
    stage: str
    start_date: date
    planned_end_date: Optional[date] = None
    status: str = "active"
    created_at: datetime
    products: list[ProjectProductResponse] = []
    phases: list[ProjectPhaseResponse] = []

    class Config:
        from_attributes = True


class ProjectCreate(BaseModel):
    name: str
    customer_name: str = ""
    stage: str = "presale"
    start_date: date
    product_ids: list[int]


class ProjectListItem(BaseModel):
    id: int
    name: str
    customer_name: str
    stage: str
    start_date: date
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectList(BaseModel):
    items: list[ProjectListItem]


class TaskUpdate(BaseModel):
    status: Optional[str] = None
    progress: Optional[int] = None
    assignee: Optional[str] = None
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    notes: Optional[str] = None
```

- [ ] **Step 5: Run import test**

```bash
cd D:\APM\backend && python -c "
from app.models.product import Product
from app.models.template import ProcessTemplate, PhaseDefinition, TaskDefinition
from app.models.project import Project, ProjectProduct, ProjectPhase, ProjectTask
print('All models defined OK')
"
```

Expected: `All models defined OK`

---

### Task 3: 种子数据 — 6 个产品及其流程模板

**Files:**
- Create: `backend/app/seed.py`

**Interfaces:**
- Produces: `init_seed_data(db: Session)` — 检查数据库是否已初始化，如果没有则写入种子数据
- Data: 6 产品 + 18+ 阶段 + 50+ 任务

- [ ] **Step 1: Create seed.py** (简化的种子数据，各产品 3-5 个阶段)

```python
from sqlalchemy.orm import Session
from app.models.product import Product
from app.models.template import ProcessTemplate, PhaseDefinition, TaskDefinition


def init_seed_data(db: Session):
    """初始化种子数据，如已存在则跳过"""
    if db.query(Product).first():
        return

    # ============ 产品定义 ============
    products = [
        Product(name="私有化企微 - 统一包", code="wecom_unified", sort_order=1),
        Product(name="私有化企微 - 定制包", code="wecom_custom", sort_order=2),
        Product(name="低代码平台", code="lowcode", sort_order=3),
        Product(name="门户", code="portal", sort_order=4),
        Product(name="纯定制化开发", code="custom_dev", sort_order=5),
        Product(name="运维服务", code="ops", sort_order=6),
    ]
    db.add_all(products)
    db.flush()

    # ============ 流程模板数据 ============
    # 每个产品定义一个模板，模板包含阶段，阶段包含任务

    seed_templates = [
        # --- 统一包企微 ---
        _make_template(db, products[0], "统一包企微部署流程", [
            _phase("项目立项准备", "组建项目团队、明确沟通机制、获取企微授权", [
                _task("1.1", "项目立项 & 组建项目团队", 2,
                      guide="明确双方项目组成员，确定项目经理。输出项目章程。",
                      deliverable="项目章程、组织架构清单", vendor_role="项目经理", customer_role="项目对接人"),
                _task("1.2", "硬件资源评估 & 环境确认", 1,
                      guide="确认企微部署所需硬件资源（服务器配置、网络带宽等）。参考统一包资源清单。",
                      deliverable="资源清单", vendor_role="实施工程师", customer_role="IT部门"),
                _task("1.3", "企微授权证书申请", 3,
                      guide="提交企微授权证书申请，填写相关表单。注意区分正式环境与测试环境。",
                      deliverable="授权证书、License", vendor_role="实施工程师", customer_role="配合盖章"),
            ]),
            _phase("基础环境搭建", "完成企微统一包的环境部署和基本配置", [
                _task("2.1", "企微统一包环境部署", 3,
                      guide="按照企微统一包部署手册进行操作。注意配置参数与客户环境匹配。",
                      deliverable="环境部署验收报告", vendor_role="实施工程师"),
                _task("2.2", "基础配置 & 初始化", 2,
                      guide="组织架构导入、用户账号初始化、基础权限配置。",
                      deliverable="配置确认单", vendor_role="实施工程师", customer_role="配合提供组织架构"),
                _task("2.3", "网络连通性测试", 1,
                      guide="验证企微客户端与服务器网络连通性，包括内外网访问测试。",
                      deliverable="网络测试报告", vendor_role="实施工程师", customer_role="IT部门配合"),
            ]),
            _phase("业务摸底与培训", "调研客户需求，组织基础培训", [
                _task("3.1", "客户业务需求调研", 2,
                      guide="了解客户使用场景，梳理核心需求。注意区分必须需求与期望需求。",
                      deliverable="需求调研记录", vendor_role="项目经理/BA", customer_role="业务部门负责人"),
                _task("3.2", "基础操作培训", 1,
                      guide="为客户管理员和用户提供企微基础操作培训。",
                      deliverable="培训签到表、培训材料", vendor_role="项目经理", customer_role="参训人员"),
            ]),
            _phase("测试与上线", "完成集成测试并正式上线", [
                _task("4.1", "集成测试", 3,
                      guide="全功能测试，包括企微客户端功能、基础应用。记录缺陷并跟踪修复。",
                      deliverable="测试报告、缺陷清单", vendor_role="测试工程师", customer_role="配合测试"),
                _task("4.2", "正式上线", 1,
                      guide="切换正式环境，确认所有功能正常。",
                      deliverable="上线确认单", vendor_role="项目经理", customer_role="客户签字确认"),
            ]),
        ]),

        # --- 定制包企微（参照徽商 Excel 简化版）---
        _make_template(db, products[1], "定制包企微部署流程", [
            _phase("项目立项准备", "项目启动、搭建组织、获取授权", [
                _task("1.1", "项目立项 & 组建项目团队", 2,
                      guide="明确双方项目成员、职责分工。输出项目章程、沟通计划。",
                      deliverable="项目章程、组织架构清单、沟通计划", vendor_role="项目经理", customer_role="项目对接人"),
                _task("1.2", "硬件资源申请 & 架构确认", 3,
                      guide="评估硬件资源需求（建议16k并发以上），确认整体技术架构。注意与客户IT部门充分沟通。",
                      deliverable="硬件资源清单、UAT/正式环境部署方案", vendor_role="实施工程师", customer_role="IT部门"),
                _task("1.3", "企微授权证书申请 & License获取", 5,
                      guide="提交企微授权证书申请，跟进审批流程。注意授权证书有有效期。",
                      deliverable="企微授权证书、License", vendor_role="项目经理", customer_role="配合提供资质文件"),
            ]),
            _phase("基础环境搭建", "搭建UAT/正式环境，完成基础配置", [
                _task("2.1", "UAT环境搭建 & 硬件部署", 2,
                      guide="部署UAT环境，完成服务器初始化。参考部署方案执行。",
                      deliverable="UAT环境验收报告", vendor_role="实施工程师", customer_role="IT部门配合"),
                _task("2.2", "企微UAT环境配置", 3,
                      guide="完成企微定制包UAT配置，包括应用管理、通讯录同步等。",
                      deliverable="环境配置单", vendor_role="实施工程师"),
                _task("2.3", "应用打包 & 上架准备", 2,
                      guide="完成定制应用打包、iOS/Android证书配置。注意上架审核周期。",
                      deliverable="安装包", vendor_role="实施工程师"),
                _task("2.4", "网络连通性与安全测试", 1,
                      guide="全面测试网络连通性，包括VPN、专线等场景。",
                      deliverable="网络测试报告", vendor_role="实施工程师"),
            ]),
            _phase("业务摸底与启动", "业务需求调研、接口规范培训", [
                _task("3.1", "业务应用系统摸底", 3,
                      guide="全面梳理客户现有业务应用系统清单，识别待集成系统。覆盖办公/业务/科技等。",
                      deliverable="应用系统盘点清单V1.0", vendor_role="BA+客户业务部门", customer_role="业务部门接口人"),
                _task("3.2", "接口规范培训 & 开发平台API培训", 2,
                      guide="组织开发平台API培训，输出接口规范手册。",
                      deliverable="培训材料、接口规范手册", vendor_role="技术经理", customer_role="开发人员参加"),
                _task("3.3", "AI需求 & 增值应用需求调研", 2,
                      guide="调研AI应用场景，包括智能客服、文档处理等。输出AI需求清单。",
                      deliverable="AI需求清单", vendor_role="AI产品经理", customer_role="业务部门"),
            ]),
            _phase("系统集成与测试", "完成应用集成、全链路测试", [
                _task("4.1", "统一入口/统一待办/统一信息集成", 5,
                      guide="完成三方应用集成，实现统一门户。注意各系统对接规范。",
                      deliverable="集成API文档", vendor_role="开发工程师", customer_role="配合提供接口文档"),
                _task("4.2", "业务应用接入（信贷/风控/OA等）", 5,
                      guide="接入各业务系统，完成接口联调。",
                      deliverable="接口联调确认单", vendor_role="开发工程师", customer_role="业务系统负责人"),
                _task("4.3", "AI智能助手 & 增值应用开发", 10,
                      guide="开发AI智能客服、智能文档处理等增值应用。聚焦高价值场景。",
                      deliverable="AI模块", vendor_role="AI开发团队", customer_role="提供业务场景样例"),
                _task("4.4", "UAT用户验收测试", 5,
                      guide="组织客户关键用户进行UAT测试，记录问题并跟踪修复。",
                      deliverable="UAT测试报告、缺陷清单", vendor_role="测试工程师", customer_role="关键用户参与"),
            ]),
            _phase("试运行与投产", "试运行验证，正式切换", [
                _task("5.1", "试运行（关键用户小范围）", 5,
                      guide="选取部分关键用户试运行，收集反馈。注意设置反馈渠道。",
                      deliverable="试运行报告", vendor_role="项目经理", customer_role="关键用户使用"),
                _task("5.2", "培训与推广", 3,
                      guide="组织全员培训，输出操作手册和视频教程。",
                      deliverable="操作手册、培训视频", vendor_role="项目经理", customer_role="参训人员"),
                _task("5.3", "正式上线", 1,
                      guide="全量切换，停止旧系统。注意数据迁移和备份。",
                      deliverable="上线确认签字单", vendor_role="项目经理", customer_role="客户签字确认"),
            ]),
        ]),

        # --- 低代码平台 ---
        _make_template(db, products[2], "低代码平台部署流程", [
            _phase("部署准备", "服务器准备、License获取", [
                _task("1.1", "低代码平台License申请", 2,
                      guide="提交License申请，确定授权范围。注意区分正式/测试License。",
                      deliverable="License文件", vendor_role="项目经理"),
                _task("1.2", "服务器环境准备", 2,
                      guide="按低代码平台部署要求准备服务器环境（JDK、数据库等）。",
                      deliverable="环境检查单", vendor_role="实施工程师", customer_role="IT部门配合"),
            ]),
            _phase("平台部署", "安装低代码平台并初始化", [
                _task("2.1", "低代码平台安装", 2,
                      guide="执行安装脚本，完成基础部署。注意初始化参数配置。",
                      deliverable="安装日志", vendor_role="实施工程师"),
                _task("2.2", "平台初始化配置", 2,
                      guide="租户创建、用户导入、基础模块启用。",
                      deliverable="配置确认单", vendor_role="实施工程师", customer_role="提供基础数据"),
                _task("2.3", "功能验证测试", 2,
                      guide="验证平台核心功能正常（表单、流程、报表）。",
                      deliverable="功能测试报告", vendor_role="测试工程师", customer_role="配合测试"),
            ]),
            _phase("培训与移交", "客户管理员培训、移交运维", [
                _task("3.1", "管理员培训", 2,
                      guide="培训客户管理员掌握平台管理、应用发布、用户管理等操作。",
                      deliverable="管理员手册", vendor_role="项目经理", customer_role="管理员参加"),
                _task("3.2", "运维移交", 1,
                      guide="移交运维文档、监控账号、备份策略等。",
                      deliverable="运维移交清单", vendor_role="实施工程师", customer_role="运维团队接收"),
            ]),
        ]),

        # --- 门户 ---
        _make_template(db, products[3], "门户部署流程", [
            _phase("部署准备", "环境检查、资源准备", [
                _task("1.1", "门户部署环境检查", 1,
                      guide="确认服务器配置满足门户部署要求。",
                      deliverable="环境检查单", vendor_role="实施工程师"),
                _task("1.2", "门户License获取", 1,
                      guide="申请门户产品License。",
                      deliverable="License文件", vendor_role="项目经理"),
            ]),
            _phase("门户部署与配置", "安装门户并完成定制配置", [
                _task("2.1", "门户安装部署", 2,
                      guide="安装门户服务，完成基础配置。",
                      deliverable="安装记录", vendor_role="实施工程师"),
                _task("2.2", "门户主题配置", 2,
                      guide="配置门户主题风格、布局、导航等。",
                      deliverable="门户配置确认单", vendor_role="实施工程师", customer_role="确认样式"),
                _task("2.3", "门户集成测试", 2,
                      guide="验证门户与各应用集成正常，页面访问、跳转、SSO正常。",
                      deliverable="集成测试报告", vendor_role="测试工程师"),
            ]),
        ]),

        # --- 纯定制化开发 ---
        _make_template(db, products[4], "纯定制开发流程", [
            _phase("需求阶段", "需求分析、原型设计", [
                _task("1.1", "需求调研与分析", 3,
                      guide="深入了解客户需求，输出需求规格说明书。注意需求变更管理。",
                      deliverable="需求规格说明书", vendor_role="BA/产品经理", customer_role="业务部门确认"),
                _task("1.2", "原型设计 & 客户确认", 3,
                      guide="输出交互原型，与客户确认UI设计和交互流程。",
                      deliverable="原型设计稿", vendor_role="UI设计师", customer_role="客户确认"),
            ]),
            _phase("开发阶段", "技术设计、编码实现", [
                _task("2.1", "技术方案设计", 2,
                      guide="系统架构设计、数据库设计、接口设计。",
                      deliverable="技术设计文档", vendor_role="技术经理"),
                _task("2.2", "编码开发", None,
                      guide="按技术方案进行编码实现，定期代码审查。承诺交付时间视需求复杂度定。",
                      deliverable="代码库", vendor_role="开发工程师"),
                _task("2.3", "单元测试 & 代码审查", 2,
                      guide="开发完成自测，代码审查，修复缺陷。",
                      deliverable="单元测试报告", vendor_role="开发工程师"),
            ]),
            _phase("交付阶段", "测试、部署、验收", [
                _task("3.1", "集成测试", 3,
                      guide="全功能集成测试，输出测试报告。",
                      deliverable="测试报告", vendor_role="测试工程师"),
                _task("3.2", "部署上线", 1,
                      guide="部署到正式环境，完成上线。",
                      deliverable="上线确认单", vendor_role="实施工程师", customer_role="客户确认"),
                _task("3.3", "验收 & 移交", 2,
                      guide="客户验收测试，验收通过后移交源码和运维文档。",
                      deliverable="验收报告、运维文档", vendor_role="项目经理", customer_role="验收签字"),
            ]),
        ]),

        # --- 运维服务 ---
        _make_template(db, products[5], "基础运维服务", [
            _phase("运维初始化", "建立运维体系", [
                _task("1.1", "运维交接", 1,
                      guide="从实施团队接收运维所需的系统信息、账号密码、架构文档。",
                      deliverable="运维交接清单", vendor_role="运维工程师", customer_role="IT部门配合"),
                _task("1.2", "监控体系搭建", 2,
                      guide="配置监控告警（Zabbix/Prometheus等），设置告警阈值。",
                      deliverable="监控配置记录", vendor_role="运维工程师"),
            ]),
            _phase("日常运维", "定期巡检、故障处理", [
                _task("2.1", "定期巡检（周/月）", None,
                      guide="按周期检查系统运行状态，输出巡检报告。注意关注磁盘、内存、CPU使用率。",
                      deliverable="巡检报告", vendor_role="运维工程师"),
                _task("2.2", "故障处理 & 应急响应", None,
                      guide="接收告警和用户报障，按SLA响应处理。",
                      deliverable="故障处理记录", vendor_role="运维工程师"),
                _task("2.3", "版本升级 & 补丁管理", None,
                      guide="按需执行系统升级和补丁更新，注意变更管理流程。",
                      deliverable="变更记录", vendor_role="运维工程师"),
            ]),
        ]),
    ]


def _phase(name, description, tasks):
    return {"name": name, "description": description, "tasks": tasks}


def _task(task_number, name, estimated_days, guide="", deliverable="",
          vendor_role="", customer_role=""):
    return {
        "task_number": task_number,
        "name": name,
        "estimated_days": estimated_days,
        "guide": guide,
        "deliverable": deliverable,
        "vendor_role": vendor_role,
        "customer_role": customer_role,
    }


def _make_template(db, product, name, phases_data):
    template = ProcessTemplate(
        product_id=product.id,
        name=name,
        version="1.0",
        is_active=True,
    )
    db.add(template)
    db.flush()

    for pi, pd in enumerate(phases_data, 1):
        phase = PhaseDefinition(
            template_id=template.id,
            phase_number=pi,
            name=pd["name"],
            description=pd["description"],
            sort_order=pi,
        )
        db.add(phase)
        db.flush()

        for ti, td in enumerate(pd["tasks"], 1):
            task = TaskDefinition(
                phase_id=phase.id,
                task_number=td["task_number"],
                name=td["name"],
                estimated_days=td["estimated_days"] if td["estimated_days"] else 0,
                guide=td["guide"],
                deliverable=td["deliverable"],
                vendor_role=td["vendor_role"],
                customer_role=td["customer_role"],
                sort_order=ti,
            )
            db.add(task)

    db.commit()
    return template
```

- [ ] **Step 2: Wire seed into startup**

Add to `backend/main.py`:
```python
# Add imports at top
from app.database import SessionLocal
from app.seed import init_seed_data

# Add after on_startup
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        init_seed_data(db)
    finally:
        db.close()
```

- [ ] **Step 3: Test seed**

```bash
cd D:\APM\backend && python -c "
from app.database import SessionLocal
from app.seed import init_seed_data
from app.models.product import Product
from app.models.template import ProcessTemplate, PhaseDefinition, TaskDefinition

db = SessionLocal()
init_seed_data(db)
products = db.query(Product).all()
templates = db.query(ProcessTemplate).all()
phases = db.query(PhaseDefinition).all()
tasks = db.query(TaskDefinition).all()

print(f'Products: {len(products)}')
for p in products:
    print(f'  - {p.name} ({p.code})')
print(f'Templates: {len(templates)}')
print(f'Phases: {len(phases)}')
print(f'Tasks: {len(tasks)}')
db.close()
"
```

Expected:
```
Products: 6
  - 私有化企微 - 统一包 (wecom_unified)
  - 私有化企微 - 定制包 (wecom_custom)
  - 低代码平台 (lowcode)
  - 门户 (portal)
  - 纯定制化开发 (custom_dev)
  - 运维服务 (ops)
Templates: 6
Phases: 18+
Tasks: 50+
```

---

### Task 4: API 路由 — Products + Templates

**Files:**
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/products.py`
- Create: `backend/app/api/templates.py`

**Interfaces:**
- Consumes: `get_db` from `database.py`, Product model, ProcessTemplate model (with relationships)
- Consumes: Pydantic schemas from `schemas/product.py`, `schemas/template.py`
- Produces: `GET /api/products` — 返回所有启用的产品列表
- Produces: `GET /api/products/{id}/template` — 返回指定产品的活跃模板（含阶段和任务）

- [ ] **Step 1: Create api/__init__.py**

Empty file:
```python
```

- [ ] **Step 2: Create api/products.py**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.product import Product
from app.schemas.product import ProductResponse, ProductList

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=ProductList)
def list_products(db: Session = Depends(get_db)):
    items = db.query(Product).filter(Product.is_active == True).order_by(Product.sort_order).all()
    return ProductList(items=items)
```

- [ ] **Step 3: Create api/templates.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.product import Product
from app.models.template import ProcessTemplate
from app.schemas.template import ProcessTemplateResponse

router = APIRouter(prefix="/api/products", tags=["templates"])


@router.get("/{product_id}/template", response_model=ProcessTemplateResponse)
def get_product_template(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    template = db.query(ProcessTemplate).filter(
        ProcessTemplate.product_id == product_id,
        ProcessTemplate.is_active == True
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="该产品暂无模板")
    return template
```

- [ ] **Step 4: Wire routers into main.py**

```python
from app.api import products as products_api
from app.api import templates as templates_api

app.include_router(products_api.router)
app.include_router(templates_api.router)
```

- [ ] **Step 5: Test APIs**

```bash
cd D:\APM\backend
uvicorn main:app --reload --port 8000 &
sleep 2

# Test products list
curl http://localhost:8000/api/products
# Expected: JSON with 6 products

# Test template for product 1 (统一包企微)
curl http://localhost:8000/api/products/1/template
# Expected: template with phases and tasks

kill %1 2>/dev/null
```

---

### Task 5: 核心引擎 — Plan Generator

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/plan_generator.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_plan_generator.py`

**Interfaces:**
- Consumes: `Session`, `Project`, `ProjectProduct`, `ProjectPhase`, `ProjectTask` models
- Consumes: `ProcessTemplate`, `PhaseDefinition`, `TaskDefinition` models
- Produces: `generate_project_plan(db: Session, project_id: int) -> Project` — 读取项目的产品组合，合并模板生成阶段和任务

- [ ] **Step 1: Create services/__init__.py** (empty)

- [ ] **Step 2: Create plan_generator.py**

```python
from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.models.project import Project, ProjectProduct, ProjectPhase, ProjectTask
from app.models.template import ProcessTemplate, PhaseDefinition, TaskDefinition


def generate_project_plan(db: Session, project_id: int) -> Project:
    """
    核心计划生成引擎。
    根据项目的产品组合，加载各产品的活跃模板，合并阶段和任务，
    以项目启动日为基准推算日期，写入数据库。
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError(f"Project {project_id} not found")

    # 1. 获取项目已关联的产品ID
    product_ids = [pp.product_id for pp in project.products]

    # 2. 获取这些产品的活跃模板，按模板加载阶段→任务
    templates = db.query(ProcessTemplate).filter(
        ProcessTemplate.product_id.in_(product_ids),
        ProcessTemplate.is_active == True
    ).all()

    if not templates:
        raise ValueError("No active templates found for selected products")

    # 3. 合并阶段：按阶段名去重合并
    phase_map = {}  # name -> (phase_obj, template_id, tasks_from_template)
    seen_orders = set()

    for template in templates:
        phases = db.query(PhaseDefinition).filter(
            PhaseDefinition.template_id == template.id
        ).order_by(PhaseDefinition.sort_order).all()

        for phase_def in phases:
            tasks = db.query(TaskDefinition).filter(
                TaskDefinition.phase_id == phase_def.id
            ).order_by(TaskDefinition.sort_order).all()

            if phase_def.name in phase_map:
                # 同名阶段合并任务
                existing = phase_map[phase_def.name]
                existing[2].extend(tasks)
            else:
                phase_map[phase_def.name] = [phase_def, template.id, list(tasks)]
                seen_orders.add(phase_def.sort_order)

    # 4. 按 sort_order 排序合并后的阶段
    sorted_phases = sorted(phase_map.items(), key=lambda x: x[1][0].sort_order)

    # 5. 创建 ProjectPhase 和 ProjectTask，推算日期
    cursor_date = project.start_date
    for pi, (phase_name, (phase_def, tmpl_id, tasks)) in enumerate(sorted_phases, 1):
        # 计算本阶段总估算天数
        total_days = sum((t.estimated_days or 1) for t in tasks) if tasks else 1

        phase_start = cursor_date
        phase_end = _add_workdays(phase_start, total_days - 1)

        proj_phase = ProjectPhase(
            project_id=project.id,
            source_phase_id=phase_def.id,
            phase_number=pi,
            name=phase_name,
            planned_start=phase_start,
            planned_end=phase_end,
            status="pending",
            sort_order=pi,
        )
        db.add(proj_phase)
        db.flush()

        # 生成任务
        task_cursor = phase_start
        for ti, task_def in enumerate(tasks, 1):
            task_days = task_def.estimated_days or 1
            task_start = task_cursor
            task_end = _add_workdays(task_start, task_days - 1)

            proj_task = ProjectTask(
                project_phase_id=proj_phase.id,
                source_task_id=task_def.id,
                task_number=task_def.task_number,
                name=task_def.name,
                guide=task_def.guide or "",
                deliverable=task_def.deliverable or "",
                assignee="",
                planned_start=task_start,
                planned_end=task_end,
                status="pending",
                progress=0,
                sort_order=ti,
            )
            db.add(proj_task)
            task_cursor = _add_workdays(task_end, 1)  # 任务之间间隔1工作日

        cursor_date = _add_workdays(phase_end, 1)

    # 6. 更新项目计划结束日期
    project.planned_end_date = _add_workdays(cursor_date, -1)
    db.commit()
    db.refresh(project)
    return project


def _add_workdays(from_date: date, days: int) -> date:
    """
    从 from_date 开始，增加 days 个工作日。
    注意：不处理法定节假日，仅跳过周六日。
    """
    current = from_date
    added = 0
    while added < days:
        current += timedelta(days=1)
        if current.weekday() < 5:  # 周一到周五
            added += 1
    return current
```

- [ ] **Step 3: Write test**

`backend/tests/conftest.py`:
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.seed import init_seed_data


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)
    session = TestingSession()
    init_seed_data(session)
    yield session
    session.close()
```

`backend/tests/test_plan_generator.py`:
```python
from datetime import date
from app.models.project import Project, ProjectProduct
from app.models.product import Product
from app.services.plan_generator import generate_project_plan


def test_generate_plan_with_single_product(db_session):
    """测试单个产品 → 生成项目计划"""
    product = db_session.query(Product).first()
    project = Project(name="测试项目", customer_name="测试客户",
                      start_date=date(2026, 8, 1), stage="signed")
    db_session.add(project)
    db_session.flush()

    db_session.add(ProjectProduct(project_id=project.id, product_id=product.id))
    db_session.commit()

    result = generate_project_plan(db_session, project.id)

    assert result.id == project.id
    assert len(result.phases) > 0
    assert result.planned_end_date is not None

    # 验证阶段有任务
    for phase in result.phases:
        assert len(phase.tasks) > 0, f"Phase '{phase.name}' has no tasks"

    print(f"Generated {len(result.phases)} phases, "
          f"{sum(len(p.tasks) for p in result.phases)} tasks")
    print(f"Project: {result.start_date} → {result.planned_end_date}")
    for p in result.phases:
        print(f"  {p.phase_number}. {p.name}: {p.planned_start} → {p.planned_end} [{p.status}]")
        for t in p.tasks:
            print(f"     {t.task_number} {t.name}: {t.planned_start} → {t.planned_end}")


def test_generate_plan_with_multiple_products(db_session):
    """测试多个产品 → 合并阶段"""
    products = db_session.query(Product).limit(2).all()
    project = Project(name="组合项目", customer_name="组合客户",
                      start_date=date(2026, 9, 1), stage="signed")
    db_session.add(project)
    db_session.flush()

    for p in products:
        db_session.add(ProjectProduct(project_id=project.id, product_id=p.id))
    db_session.commit()

    result = generate_project_plan(db_session, project.id)

    assert len(result.phases) > 0
    assert result.planned_end_date is not None
    print(f"\nMulti-product: {len(result.phases)} phases merged")
    for p in result.phases:
        print(f"  {p.phase_number}. {p.name}: {len(p.tasks)} tasks")
```

- [ ] **Step 4: Run tests**

```bash
cd D:\APM\backend
pip install pytest
python -m pytest tests/test_plan_generator.py -v
```

Expected: Both tests PASS, showing phases with tasks and calculated dates.

---

### Task 6: API 路由 — Projects CRUD

**Files:**
- Create: `backend/app/api/projects.py`

**Interfaces:**
- Consumes: `Project`, `ProjectProduct`, `ProjectPhase`, `ProjectTask` models
- Consumes: `generate_project_plan()` from services
- Produces: `POST /api/projects` — 创建项目并为勾选的产品生成计划
- Produces: `GET /api/projects` — 项目列表
- Produces: `GET /api/projects/{id}` — 项目详情（含阶段和任务）
- Produces: `PUT /api/projects/{id}/tasks/{task_id}` — 更新任务状态/进度
- Produces: `GET /api/projects/{id}/phases` — 阶段列表

- [ ] **Step 1: Create projects.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.project import Project, ProjectProduct, ProjectTask
from app.models.product import Product
from app.schemas.project import (
    ProjectCreate, ProjectResponse, ProjectList, ProjectListItem,
    TaskUpdate, ProjectPhaseResponse
)
from app.services.plan_generator import generate_project_plan

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    """创建项目，选择产品组合，自动生成项目计划"""
    # 验证产品存在
    products = db.query(Product).filter(
        Product.id.in_(data.product_ids),
        Product.is_active == True
    ).all()
    if len(products) != len(data.product_ids):
        raise HTTPException(status_code=400, detail="部分产品不存在或已禁用")

    # 创建项目
    project = Project(
        name=data.name,
        customer_name=data.customer_name,
        stage=data.stage,
        start_date=data.start_date,
        status="active",
    )
    db.add(project)
    db.flush()

    # 关联产品
    for pid in data.product_ids:
        db.add(ProjectProduct(project_id=project.id, product_id=pid))
    db.commit()

    # 自动生成计划
    try:
        project = generate_project_plan(db, project.id)
    except ValueError as e:
        db.delete(project)
        db.commit()
        raise HTTPException(status_code=400, detail=str(e))

    return project


@router.get("", response_model=ProjectList)
def list_projects(db: Session = Depends(get_db)):
    items = db.query(Project).order_by(Project.created_at.desc()).all()
    return ProjectList(items=items)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


@router.put("/{project_id}/tasks/{task_id}")
def update_task(project_id: int, task_id: int, data: TaskUpdate,
               db: Session = Depends(get_db)):
    task = db.query(ProjectTask).filter(
        ProjectTask.id == task_id,
        ProjectTask.phase.has(project_id=project_id)
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if data.status is not None:
        task.status = data.status
    if data.progress is not None:
        task.progress = max(0, min(100, data.progress))
    if data.assignee is not None:
        task.assignee = data.assignee
    if data.actual_start is not None:
        task.actual_start = data.actual_start
    if data.actual_end is not None:
        task.actual_end = data.actual_end
    if data.notes is not None:
        task.notes = data.notes

    db.commit()
    return {"message": "ok"}


@router.get("/{project_id}/phases", response_model=list[ProjectPhaseResponse])
def list_phases(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project.phases
```

`backend/app/schemas/__init__.py`:
```python
from .product import ProductResponse, ProductList
from .template import ProcessTemplateResponse, PhaseDefinitionResponse, TaskDefinitionResponse
from .project import (
    ProjectCreate, ProjectResponse, ProjectList, ProjectListItem,
    ProjectPhaseResponse, ProjectTaskResponse, TaskUpdate
)
```

- [ ] **Step 2: Wire into main.py**

```python
from app.api import projects as projects_api
app.include_router(projects_api.router)
```

- [ ] **Step 3: Test API**

```bash
cd D:\APM\backend
uvicorn main:app --reload --port 8000 &
sleep 2

# Create project with product 1 (统一包企微) and product 3 (低代码平台)
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -d '{"name":"测试项目","customer_name":"测试客户","start_date":"2026-08-01","product_ids":[1,3]}'
# Expected: 201, full project with phases and tasks

# List projects
curl http://localhost:8000/api/projects

# Get project detail (replace {id} with actual id)
curl http://localhost:8000/api/projects/1

# Get phases
curl http://localhost:8000/api/projects/1/phases

# Update task status (replace {task_id} with actual task id)
curl -X PUT http://localhost:8000/api/projects/1/tasks/{task_id} \
  -H "Content-Type: application/json" \
  -d '{"status":"in_progress","progress":30}'

kill %1 2>/dev/null
```

---

### Task 7: 前端脚手架 — Vue3 + Element Plus + Vite + Router

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/env.d.ts`
- Create: `frontend/index.html`
- Create: `frontend/src/main.ts`
- Create: `frontend/src/App.vue`
- Create: `frontend/src/style.css`
- Create: `frontend/src/router/index.ts`
- Create: `frontend/src/api/index.ts`

**Interfaces:**
- Consumes: Backend API at `http://localhost:8000`
- Produces: Running Vue3 app at `http://localhost:5173`

- [ ] **Step 1: Create package.json**

```json
{
  "name": "ccb-frontend",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc --noEmit && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.5.0",
    "vue-router": "^4.4.0",
    "element-plus": "^2.8.0",
    "@element-plus/icons-vue": "^2.3.0",
    "axios": "^1.7.0",
    "pinia": "^2.2.0",
    "dayjs": "^1.11.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.1.0",
    "typescript": "^5.5.0",
    "vite": "^5.4.0",
    "vue-tsc": "^2.1.0"
  }
}
```

- [ ] **Step 2: Create vite.config.ts**

```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

- [ ] **Step 3: Create tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "preserve",
    "strict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noFallthroughCasesInSwitch": true,
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src/**/*.ts", "src/**/*.tsx", "src/**/*.vue", "env.d.ts"]
}
```

- [ ] **Step 4: Create tsconfig.node.json**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2023"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "strict": true
  },
  "include": ["vite.config.ts"]
}
```

- [ ] **Step 5: Create env.d.ts**

```typescript
/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}
```

- [ ] **Step 6: Create index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>CCB 项目管理系统</title>
</head>
<body>
  <div id="app"></div>
  <script type="module" src="/src/main.ts"></script>
</body>
</html>
```

- [ ] **Step 7: Create src/main.ts**

```typescript
import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './style.css'

const app = createApp(App)

// Register all Element Plus icons
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(ElementPlus, { locale: zhCn })
app.use(createPinia())
app.use(router)
app.mount('#app')
```

- [ ] **Step 8: Create src/style.css**

```css
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.app-container {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  width: 260px;
  min-width: 260px;
  background: #f5f7fa;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #fff;
}
```

- [ ] **Step 9: Create src/App.vue**

```vue
<template>
  <div class="app-container">
    <div class="sidebar">
      <div style="padding: 16px; border-bottom: 1px solid #e4e7ed;">
        <h2 style="font-size: 18px; margin: 0;">
          <el-icon style="vertical-align: middle;"><Menu /></el-icon>
          CCB 项目管理系统
        </h2>
      </div>
      <el-menu
        router
        :default-active="route.path"
        style="border-right: none;"
      >
        <el-menu-item index="/">
          <el-icon><List /></el-icon>
          <span>项目列表</span>
        </el-menu-item>
        <el-menu-item index="/projects/new">
          <el-icon><Plus /></el-icon>
          <span>新建项目</span>
        </el-menu-item>
      </el-menu>
    </div>
    <div class="main-content">
      <router-view />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
const route = useRoute()
</script>
```

- [ ] **Step 10: Create router/index.ts**

```typescript
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'project-list',
      component: () => import('@/views/ProjectList.vue'),
    },
    {
      path: '/projects/new',
      name: 'project-new',
      component: () => import('@/views/ProjectNew.vue'),
    },
    {
      path: '/projects/:id',
      name: 'project-detail',
      component: () => import('@/views/ProjectDetail.vue'),
      props: true,
    },
  ],
})

export default router
```

- [ ] **Step 11: Create api/index.ts**

```typescript
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
})

export default api
```

- [ ] **Step 12: Install and verify**

```bash
cd D:\APM\frontend
npm install
npm run dev
```

Open browser to `http://localhost:5173`. Expected: App loads with sidebar and empty main content (不会看到实际页面，因为 views 还没有内容）。

---

### Task 8: 前端页面 — 项目列表 + 新建项目

**Files:**
- Create: `frontend/src/stores/project.ts`
- Create: `frontend/src/api/products.ts`
- Create: `frontend/src/api/projects.ts`
- Create: `frontend/src/views/ProjectList.vue`
- Create: `frontend/src/views/ProjectNew.vue`

**Interfaces:**
- Consumes: `GET /api/projects`, `POST /api/projects`, `GET /api/products` API endpoints
- Produces: Project list with cards/table, new project form with product checkbox selection

- [ ] **Step 1: Create stores/project.ts**

```typescript
import { defineStore } from 'pinia'
import api from '@/api'
import type { Project, ProjectListItem } from '@/api/projects'

interface ProjectState {
  projects: ProjectListItem[]
  currentProject: Project | null
  loading: boolean
}

export const useProjectStore = defineStore('project', {
  state: (): ProjectState => ({
    projects: [],
    currentProject: null,
    loading: false,
  }),
  actions: {
    async fetchProjects() {
      this.loading = true
      try {
        const res = await api.get('/projects')
        this.projects = res.data.items
      } finally {
        this.loading = false
      }
    },
    async fetchProject(id: number) {
      this.loading = true
      try {
        const res = await api.get(`/projects/${id}`)
        this.currentProject = res.data
      } finally {
        this.loading = false
      }
    },
  },
})
```

- [ ] **Step 2: Create api/products.ts**

```typescript
export interface Product {
  id: number
  name: string
  code: string
  description: string
  sort_order: number
}

import api from './index'

export async function fetchProducts(): Promise<Product[]> {
  const res = await api.get('/products')
  return res.data.items
}
```

- [ ] **Step 3: Create api/projects.ts**

```typescript
export interface ProjectTask {
  id: number
  project_phase_id: number
  task_number: string
  name: string
  guide: string
  deliverable: string
  assignee: string
  planned_start: string | null
  planned_end: string | null
  actual_start: string | null
  actual_end: string | null
  status: string
  progress: number
  notes: string
  sort_order: number
}

export interface ProjectPhase {
  id: number
  phase_number: number
  name: string
  planned_start: string | null
  planned_end: string | null
  status: string
  sort_order: number
  tasks: ProjectTask[]
}

export interface Project {
  id: number
  name: string
  customer_name: string
  stage: string
  start_date: string
  planned_end_date: string | null
  status: string
  created_at: string
  products: { product_id: number }[]
  phases: ProjectPhase[]
}

export interface ProjectListItem {
  id: number
  name: string
  customer_name: string
  stage: string
  start_date: string
  status: string
  created_at: string
}

export interface ProjectCreate {
  name: string
  customer_name: string
  stage: string
  start_date: string
  product_ids: number[]
}

import api from './index'

export async function createProject(data: ProjectCreate): Promise<Project> {
  const res = await api.post('/projects', data)
  return res.data
}
```

- [ ] **Step 4: Create ProjectList.vue**

```vue
<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
      <h1 style="font-size: 24px;">项目列表</h1>
      <el-button type="primary" @click="$router.push('/projects/new')">
        <el-icon><Plus /></el-icon> 新建项目
      </el-button>
    </div>

    <el-table :data="store.projects" v-loading="store.loading" stripe style="width: 100%">
      <el-table-column prop="name" label="项目名称" min-width="200" />
      <el-table-column prop="customer_name" label="客户名称" width="150" />
      <el-table-column prop="stage" label="阶段" width="120">
        <template #default="{ row }">
          <el-tag :type="stageTagType(row.stage)" size="small">
            {{ stageLabel(row.stage) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="start_date" label="启动日期" width="120" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
            {{ row.status === 'active' ? '进行中' : '已暂停' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button type="primary" link size="small" @click="$router.push(`/projects/${row.id}`)">
            查看详情
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useProjectStore } from '@/stores/project'

const store = useProjectStore()

onMounted(() => {
  store.fetchProjects()
})

function stageTagType(stage: string) {
  const map: Record<string, string> = {
    presale: 'warning',
    signed: 'info',
    executing: 'primary',
    delivered: 'success',
    archived: '',
  }
  return map[stage] || 'info'
}

function stageLabel(stage: string) {
  const map: Record<string, string> = {
    presale: '售前',
    signed: '已签约',
    executing: '执行中',
    delivered: '已交付',
    archived: '已归档',
  }
  return map[stage] || stage
}
</script>
```

- [ ] **Step 5: Create ProjectNew.vue**

```vue
<template>
  <div style="max-width: 700px; margin: 0 auto;">
    <h1 style="font-size: 24px; margin-bottom: 24px;">新建项目</h1>

    <el-form :model="form" label-width="100px" v-loading="submitting">
      <el-form-item label="项目名称" required>
        <el-input v-model="form.name" placeholder="请输入项目名称" />
      </el-form-item>

      <el-form-item label="客户名称">
        <el-input v-model="form.customer_name" placeholder="请输入客户名称" />
      </el-form-item>

      <el-form-item label="项目阶段" required>
        <el-select v-model="form.stage" style="width: 100%">
          <el-option label="售前" value="presale" />
          <el-option label="已签约" value="signed" />
          <el-option label="执行中" value="executing" />
          <el-option label="已交付" value="delivered" />
          <el-option label="已归档" value="archived" />
        </el-select>
      </el-form-item>

      <el-form-item label="启动日期" required>
        <el-date-picker v-model="form.start_date" type="date" placeholder="选择日期"
                        value-format="YYYY-MM-DD" style="width: 100%" />
      </el-form-item>

      <el-form-item label="产品组合" required>
        <el-checkbox-group v-model="form.product_ids">
          <div v-for="p in products" :key="p.id" style="margin-bottom: 8px;">
            <el-checkbox :label="p.id" :value="p.id">
              <span style="font-weight: 500;">{{ p.name }}</span>
              <span style="color: #999; font-size: 12px; margin-left: 8px;">{{ p.description }}</span>
            </el-checkbox>
          </div>
        </el-checkbox-group>
      </el-form-item>

      <el-form-item>
        <el-button type="primary" @click="handleSubmit" :disabled="!isValid">
          {{ submitting ? '创建中...' : '创建项目 & 生成计划' }}
        </el-button>
        <el-button @click="$router.push('/')">取消</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { fetchProducts, type Product } from '@/api/products'
import { createProject } from '@/api/projects'

const router = useRouter()
const products = ref<Product[]>([])
const submitting = ref(false)

const form = ref({
  name: '',
  customer_name: '',
  stage: 'signed',
  start_date: '',
  product_ids: [] as number[],
})

const isValid = computed(() => form.value.name && form.value.start_date && form.value.product_ids.length > 0)

onMounted(async () => {
  try {
    products.value = await fetchProducts()
  } catch {
    ElMessage.error('加载产品列表失败')
  }
})

async function handleSubmit() {
  if (!isValid.value) return
  submitting.value = true
  try {
    const project = await createProject({
      name: form.value.name,
      customer_name: form.value.customer_name,
      stage: form.value.stage,
      start_date: form.value.start_date,
      product_ids: form.value.product_ids,
    })
    ElMessage.success('项目创建成功，计划已生成！')
    router.push(`/projects/${project.id}`)
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '创建失败')
  } finally {
    submitting.value = false
  }
}
</script>
```

- [ ] **Step 6: Verify pages load**

```bash
cd D:\APM\frontend
npm run dev
```

Navigate to `http://localhost:5173`. Test:
- 项目列表页加载 ✅
- 点击"新建项目"进入表单 ✅
- 产品列表从 API 加载 ✅
- 选择产品、填信息、提交后跳转到项目详情（待 Task 9 实现详情页）
- 如果后端没在跑，前端会有错误提示但不崩

---

### Task 9: 前端页面 — 项目详情 + 阶段/任务列表

**Files:**
- Create: `frontend/src/views/ProjectDetail.vue`
- Create: `frontend/src/components/PhaseCard.vue`
- Create: `frontend/src/components/TaskItem.vue`
- Create: `frontend/src/api/tasks.ts`

**Interfaces:**
- Consumes: `GET /api/projects/{id}`, `PUT /api/projects/{id}/tasks/{task_id}`
- Produces: Project detail page with phase expansion, task status update

- [ ] **Step 1: Create api/tasks.ts**

```typescript
export interface TaskUpdate {
  status?: string
  progress?: number
  assignee?: string
  actual_start?: string
  actual_end?: string
  notes?: string
}

import api from './index'

export async function updateTask(projectId: number, taskId: number, data: TaskUpdate) {
  const res = await api.put(`/projects/${projectId}/tasks/${taskId}`, data)
  return res.data
}
```

- [ ] **Step 2: Create PhaseCard.vue**

```vue
<template>
  <el-card class="phase-card" shadow="never">
    <template #header>
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
          <span style="font-weight: 600; font-size: 15px;">
            阶段{{ phase.phase_number }}：{{ phase.name }}
          </span>
          <el-tag :type="statusType" size="small" style="margin-left: 8px;">
            {{ statusLabel }}
          </el-tag>
        </div>
        <span style="color: #999; font-size: 13px;">
          {{ phase.planned_start }} → {{ phase.planned_end }}
        </span>
      </div>
    </template>

    <!-- 任务列表 -->
    <div v-for="task in phase.tasks" :key="task.id" style="margin-bottom: 8px;">
      <TaskItem :task="task" @update="handleTaskUpdate" />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ProjectPhase, ProjectTask } from '@/api/projects'
import { updateTask } from '@/api/tasks'
import TaskItem from './TaskItem.vue'

const props = defineProps<{ phase: ProjectPhase }>()
const emit = defineEmits<{ refresh: [] }>()

const statusType = computed(() => {
  const map: Record<string, string> = {
    pending: 'info', in_progress: 'primary', completed: 'success', delayed: 'danger',
  }
  return map[props.phase.status] || 'info'
})

const statusLabel = computed(() => {
  const map: Record<string, string> = {
    pending: '待开始', in_progress: '进行中', completed: '已完成', delayed: '已延期',
  }
  return map[props.phase.status] || props.phase.status
})

async function handleTaskUpdate(taskId: number, data: any) {
  // 假设 projectId 从 route 获取，这里用 emit 向上冒泡
}
</script>

<style scoped>
.phase-card {
  margin-bottom: 16px;
  border: 1px solid #e4e7ed;
}
</style>
```

- [ ] **Step 3: Create TaskItem.vue**

```vue
<template>
  <div class="task-item" :class="{ 'task-completed': task.status === 'completed' }">
    <div style="display: flex; align-items: flex-start; gap: 12px;">
      <!-- 状态切换 -->
      <el-checkbox
        :model-value="task.status === 'completed'"
        @change="toggleComplete"
        :disabled="task.status === 'blocked'"
      />

      <!-- 任务信息 -->
      <div style="flex: 1; min-width: 0;">
        <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
          <span style="color: #666; font-size: 12px; font-family: monospace;">{{ task.task_number }}</span>
          <span class="task-name">{{ task.name }}</span>
          <el-tag :type="taskStatusType" size="small">{{ taskStatusLabel }}</el-tag>
        </div>

        <!-- 操作指引下拉 -->
        <div v-if="task.guide" style="margin-top: 4px;">
          <el-popover trigger="click" :width="400">
            <template #reference>
              <el-button link size="small" type="primary" style="font-size: 12px;">
                查看指引
              </el-button>
            </template>
            <div style="white-space: pre-wrap; font-size: 13px; line-height: 1.6;">
              {{ task.guide }}
            </div>
          </el-popover>
        </div>

        <!-- 日期和负责人 -->
        <div style="display: flex; gap: 16px; margin-top: 4px; font-size: 12px; color: #999;">
          <span>计划: {{ task.planned_start }} → {{ task.planned_end }}</span>
          <span>负责人: <el-input v-model="task.assignee" size="small" style="width: 120px;"
                    @blur="updateField('assignee', task.assignee)" /></span>
          <span>进度: <el-progress :percentage="task.progress" :width="80" :stroke-width="12"
                    style="display: inline-block;" /></span>
        </div>

        <!-- 交付物 -->
        <div v-if="task.deliverable" style="margin-top: 4px; font-size: 12px; color: #409eff;">
          输出物：{{ task.deliverable }}
        </div>
      </div>

      <!-- 进度编辑 -->
      <el-button link size="small" @click="showProgressEditor = true" style="flex-shrink: 0;">
        {{ task.progress }}%
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import type { ProjectTask } from '@/api/projects'
import { updateTask } from '@/api/tasks'

const props = defineProps<{
  task: ProjectTask
  projectId: number
}>()

const emit = defineEmits<{ refresh: [] }>()
const showProgressEditor = ref(false)

const taskStatusType = computed(() => {
  const map: Record<string, string> = { pending: 'info', in_progress: 'warning', completed: 'success', blocked: 'danger' }
  return map[props.task.status] || 'info'
})

const taskStatusLabel = computed(() => {
  const map: Record<string, string> = { pending: '待开始', in_progress: '进行中', completed: '已完成', blocked: '阻塞' }
  return map[props.task.status] || props.task.status
})

async function toggleComplete(checked: boolean) {
  await doUpdate({
    status: checked ? 'completed' : 'pending',
    progress: checked ? 100 : 0,
    actual_end: checked ? new Date().toISOString().split('T')[0] : null,
  })
}

async function updateField(field: string, value: any) {
  await doUpdate({ [field]: value })
}

async function doUpdate(data: any) {
  try {
    await updateTask(props.projectId, props.task.id, data)
    emit('refresh')
  } catch {
    ElMessage.error('更新失败')
  }
}
</script>

<style scoped>
.task-item {
  padding: 10px 12px;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  background: #fafafa;
}
.task-item:hover {
  background: #f0f5ff;
  border-color: #409eff;
}
.task-completed {
  opacity: 0.7;
}
.task-completed .task-name {
  text-decoration: line-through;
  color: #999;
}
.task-name {
  font-size: 14px;
  font-weight: 500;
}
</style>
```

- [ ] **Step 4: Create ProjectDetail.vue**

```vue
<template>
  <div v-loading="store.loading">
    <div v-if="project" style="max-width: 960px; margin: 0 auto;">
      <!-- 项目头部 -->
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <div>
          <el-button link @click="$router.push('/')" style="margin-bottom: 8px;">
            <el-icon><ArrowLeft /></el-icon> 返回列表
          </el-button>
          <h1 style="font-size: 22px;">{{ project.name }}</h1>
          <div style="color: #666; font-size: 14px; margin-top: 4px;">
            客户：{{ project.customer_name }} |
            阶段：<el-tag :type="stageTagType" size="small">{{ stageLabel }}</el-tag> |
            时间：{{ project.start_date }} → {{ project.planned_end_date || '待定' }}
          </div>
        </div>
      </div>

      <!-- 进度概览 -->
      <el-card shadow="never" style="margin-bottom: 20px;">
        <div style="display: flex; gap: 32px;">
          <div>
            <div style="font-size: 12px; color: #999;">总阶段</div>
            <div style="font-size: 24px; font-weight: 600;">{{ project.phases.length }}</div>
          </div>
          <div>
            <div style="font-size: 12px; color: #999;">总任务</div>
            <div style="font-size: 24px; font-weight: 600;">{{ totalTasks }}</div>
          </div>
          <div>
            <div style="font-size: 12px; color: #999;">已完成</div>
            <div style="font-size: 24px; font-weight: 600; color: #67c23a;">{{ completedTasks }}</div>
          </div>
          <div>
            <div style="font-size: 12px; color: #999;">整体进度</div>
            <div style="width: 160px; margin-top: 8px;">
              <el-progress :percentage="overallProgress" :stroke-width="16" />
            </div>
          </div>
        </div>
      </el-card>

      <!-- 阶段列表 -->
      <PhaseCard
        v-for="phase in project.phases"
        :key="phase.id"
        :phase="phase"
        :project-id="project.id"
        @refresh="refreshProject"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import PhaseCard from '@/components/PhaseCard.vue'

const route = useRoute()
const store = useProjectStore()

const project = computed(() => store.currentProject)
const projectId = computed(() => Number(route.params.id))

const totalTasks = computed(() => {
  return project.value?.phases.reduce((sum, p) => sum + p.tasks.length, 0) || 0
})

const completedTasks = computed(() => {
  return project.value?.phases.reduce((sum, p) =>
    sum + p.tasks.filter(t => t.status === 'completed').length, 0
  ) || 0
})

const overallProgress = computed(() => {
  if (!totalTasks.value) return 0
  return Math.round(completedTasks.value / totalTasks.value * 100)
})

const stageLabel = computed(() => {
  const map: Record<string, string> = { presale: '售前', signed: '已签约', executing: '执行中', delivered: '已交付', archived: '已归档' }
  return map[project.value?.stage || ''] || project.value?.stage
})

const stageTagType = computed(() => {
  const map: Record<string, string> = { presale: 'warning', signed: 'info', executing: 'primary', delivered: 'success', archived: '' }
  return map[project.value?.stage || ''] || 'info'
})

onMounted(() => {
  store.fetchProject(projectId.value)
})

function refreshProject() {
  store.fetchProject(projectId.value)
}
</script>
```

- [ ] **Step 5: Fix PhaseCard to pass projectId**

Update `PhaseCard.vue` template header to add `projectId` as prop. Add to script:

```vue
const props = defineProps<{
  phase: ProjectPhase
  projectId: number
}>()
```

- [ ] **Step 6: Full integration test**

```bash
# Start backend (from D:\APM\backend)
uvicorn main:app --reload --port 8000

# In another terminal, start frontend (from D:\APM\frontend)
npm run dev
```

End-to-end test:
1. Open `http://localhost:5173` → 项目列表（空）
2. 点击"新建项目" → 填写表单
3. 选择"私有化企微 - 定制包" + "低代码平台"
4. 点击"创建项目 & 生成计划"
5. 自动跳转到项目详情页 → 看到合并后的阶段和任务列表
6. 点击任务的 checkbox 完成某任务
7. 修改负责人，整体进度自动更新

---

## 自审查清单

- [ ] Spec 覆盖度：Phase 1 MVP 覆盖了 spec 中"核心引擎 MVP"的全部要求（数据模型、种子数据、新建项目选产品、计划自动生成、阶段/任务列表、状态更新、SQLite）
- [ ] 无占位符——每个步骤都包含完整代码和命令
- [ ] 类型一致性——所有接口方法名和签名在 tasks 间一致（如 `generate_project_plan(db, project_id)` 在第5、6任务中一致使用）
- [ ] 未超出 Phase 1 范围（没有 AI 面板、文档树、看板等 Phase 2/3 内容）
