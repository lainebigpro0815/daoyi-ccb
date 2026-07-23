"""独立项目模板管理 — 不绑定产品"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload
from pydantic import BaseModel
from typing import Optional
from datetime import date
from app.database import get_db
from app.models.template import ProcessTemplate, PhaseDefinition, TaskDefinition
from app.models.project import Project, ProjectPhase, ProjectTask
from app.models.product import Product

router = APIRouter(prefix="/api/templates", tags=["templates"])


# ── Schemas ──

class TaskDefSchema(BaseModel):
    name: str
    task_number: str = ""
    guide: str = ""
    deliverable: str = ""
    vendor_role: str = ""
    customer_role: str = ""
    estimated_days: float = 1.0
    sort_order: int = 0

class PhaseDefSchema(BaseModel):
    phase_number: int
    name: str
    description: str = ""
    sort_order: int = 0
    tasks: list[TaskDefSchema] = []

class TemplateCreate(BaseModel):
    name: str
    product_id: int = 0
    version: str = "1.0"
    phases: list[PhaseDefSchema] = []

class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    version: Optional[str] = None
    is_active: Optional[bool] = None

class TemplateApply(BaseModel):
    project_id: int
    start_date: str  # "2026-08-01"


# ── CRUD ──

@router.get("")
def list_templates(db: Session = Depends(get_db)):
    templates = db.query(ProcessTemplate).options(
        selectinload(ProcessTemplate.phases).selectinload(PhaseDefinition.tasks)
    ).order_by(ProcessTemplate.id.desc()).all()
    return templates

@router.get("/{template_id}")
def get_template(template_id: int, db: Session = Depends(get_db)):
    tpl = db.query(ProcessTemplate).options(
        selectinload(ProcessTemplate.phases).selectinload(PhaseDefinition.tasks)
    ).filter(ProcessTemplate.id == template_id).first()
    if not tpl:
        raise HTTPException(404, "模板不存在")
    return tpl

@router.post("")
def create_template(body: TemplateCreate, db: Session = Depends(get_db)):
    tpl = ProcessTemplate(
        name=body.name,
        product_id=body.product_id or 1,
        version=body.version,
        is_active=True,
    )
    db.add(tpl)
    db.flush()

    for i, ps in enumerate(body.phases):
        phase = PhaseDefinition(
            template_id=tpl.id,
            phase_number=ps.phase_number or i + 1,
            name=ps.name,
            description=ps.description,
            sort_order=ps.sort_order or i,
        )
        db.add(phase)
        db.flush()

        for j, ts in enumerate(ps.tasks):
            task = TaskDefinition(
                phase_id=phase.id,
                task_number=ts.task_number or f"{ps.phase_number}.{j + 1}",
                name=ts.name,
                guide=ts.guide,
                deliverable=ts.deliverable,
                vendor_role=ts.vendor_role,
                customer_role=ts.customer_role,
                estimated_days=ts.estimated_days,
                sort_order=ts.sort_order or j,
            )
            db.add(task)

    db.commit()
    db.refresh(tpl)
    return tpl

@router.put("/{template_id}")
def update_template(template_id: int, body: TemplateUpdate, db: Session = Depends(get_db)):
    tpl = db.query(ProcessTemplate).filter(ProcessTemplate.id == template_id).first()
    if not tpl:
        raise HTTPException(404, "模板不存在")
    if body.name is not None: tpl.name = body.name
    if body.version is not None: tpl.version = body.version
    if body.is_active is not None: tpl.is_active = body.is_active
    db.commit()
    return {"status": "ok"}

@router.delete("/{template_id}")
def delete_template(template_id: int, db: Session = Depends(get_db)):
    tpl = db.query(ProcessTemplate).filter(ProcessTemplate.id == template_id).first()
    if not tpl:
        raise HTTPException(404, "模板不存在")
    # Cascade delete phases & tasks
    for phase in tpl.phases:
        db.query(TaskDefinition).filter(TaskDefinition.phase_id == phase.id).delete()
    db.query(PhaseDefinition).filter(PhaseDefinition.template_id == template_id).delete()
    db.delete(tpl)
    db.commit()
    return {"status": "deleted"}

@router.put("/{template_id}/phases")
def replace_phases(template_id: int, body: TemplateCreate, db: Session = Depends(get_db)):
    """替换模板的全部阶段和任务"""
    tpl = db.query(ProcessTemplate).filter(ProcessTemplate.id == template_id).first()
    if not tpl:
        raise HTTPException(404, "模板不存在")

    # 删除旧阶段和任务
    for phase in tpl.phases:
        db.query(TaskDefinition).filter(TaskDefinition.phase_id == phase.id).delete()
    db.query(PhaseDefinition).filter(PhaseDefinition.template_id == template_id).delete()

    # 创建新阶段和任务
    for i, ps in enumerate(body.phases):
        phase = PhaseDefinition(
            template_id=tpl.id,
            phase_number=ps.phase_number or i + 1,
            name=ps.name,
            description=ps.description,
            sort_order=ps.sort_order or i,
        )
        db.add(phase)
        db.flush()

        for j, ts in enumerate(ps.tasks):
            task = TaskDefinition(
                phase_id=phase.id,
                task_number=ts.task_number or f"{ps.phase_number}.{j + 1}",
                name=ts.name,
                guide=ts.guide,
                deliverable=ts.deliverable,
                vendor_role=ts.vendor_role,
                customer_role=ts.customer_role,
                estimated_days=ts.estimated_days,
                sort_order=ts.sort_order or j,
            )
            db.add(task)

    db.commit()
    db.refresh(tpl)
    return tpl


@router.post("/{template_id}/apply")
def apply_template(template_id: int, body: TemplateApply, db: Session = Depends(get_db)):
    """将模板应用到项目：生成阶段 + 任务"""
    tpl = db.query(ProcessTemplate).options(
        selectinload(ProcessTemplate.phases).selectinload(PhaseDefinition.tasks)
    ).filter(ProcessTemplate.id == template_id).first()
    if not tpl:
        raise HTTPException(404, "模板不存在")

    project = db.query(Project).filter(Project.id == body.project_id).first()
    if not project:
        raise HTTPException(404, "项目不存在")

    # 清理已有阶段任务（重新生成）
    existing_phases = db.query(ProjectPhase).filter(ProjectPhase.project_id == project.id).all()
    for p in existing_phases:
        db.query(ProjectTask).filter(ProjectTask.project_phase_id == p.id).delete()
    db.query(ProjectPhase).filter(ProjectPhase.project_id == project.id).delete()

    start = date.fromisoformat(body.start_date) if body.start_date else project.start_date
    cursor = start

    for td in tpl.phases:
        phase = ProjectPhase(
            project_id=project.id,
            phase_number=td.phase_number,
            name=td.name,
            status="pending",
            planned_start=cursor,
            planned_end=None,
            sort_order=td.sort_order,
        )
        db.add(phase)
        db.flush()

        for tsk in td.tasks:
            task = ProjectTask(
                project_phase_id=phase.id,
                task_number=tsk.task_number,
                name=tsk.name,
                status="pending",
                progress=0,
                planned_start=cursor,
                planned_end=None,
                sort_order=tsk.sort_order,
            )
            db.add(task)

        # 估算结束日期
        total_days = sum((t.estimated_days or 1) for t in td.tasks)
        import datetime
        end = cursor + datetime.timedelta(days=int(total_days))
        phase.planned_end = end
        cursor = end + datetime.timedelta(days=1)

    project.planned_end_date = cursor
    db.commit()
    return {"status": "applied", "project_id": project.id}
