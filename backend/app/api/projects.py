from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.project import Project, ProjectProduct, ProjectTask
from app.models.product import Product
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectList, ProjectListItem,
    TaskUpdate, ProjectPhaseResponse
)
from app.models.stakeholder import Stakeholder
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
    # Attach stakeholders
    project.__dict__["stakeholders"] = db.query(Stakeholder).filter(
        Stakeholder.project_id == project_id).all()
    return project


@router.put("/{project_id}")
def update_project(project_id: int, data: ProjectUpdate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(project, k, v)
    db.commit()
    return {"message": "ok"}


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
    if data.name is not None:
        task.name = data.name

    db.commit()
    return {"message": "ok"}


@router.post("/{project_id}/tasks", status_code=201)
def create_task(project_id: int, db: Session = Depends(get_db)):
    """在当前项目第一个阶段下添加新任务"""
    from app.models.project import ProjectPhase, ProjectTask
    phase = db.query(ProjectPhase).filter(
        ProjectPhase.project_id == project_id
    ).order_by(ProjectPhase.sort_order).first()
    if not phase:
        raise HTTPException(status_code=400, detail="项目无阶段")
    task = ProjectTask(
        project_phase_id=phase.id,
        task_number="N",
        name="新任务",
        status="pending",
    )
    db.add(task)
    db.commit()
    return task


@router.delete("/{project_id}/tasks/{task_id}")
def delete_task(project_id: int, task_id: int, db: Session = Depends(get_db)):
    from app.models.project import ProjectTask
    task = db.query(ProjectTask).filter(
        ProjectTask.id == task_id,
        ProjectTask.phase.has(project_id=project_id)
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    db.delete(task)
    db.commit()
    return {"status": "ok"}


@router.get("/{project_id}/phases", response_model=list[ProjectPhaseResponse])
def list_phases(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project.phases
