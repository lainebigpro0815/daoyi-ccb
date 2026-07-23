"""逾期任务查询 + 提醒"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date
from app.database import get_db
from app.models.project import Project, ProjectPhase, ProjectTask

router = APIRouter(prefix="/api", tags=["overdue"])


@router.get("/overdue")
def get_overdue_tasks(db: Session = Depends(get_db)):
    """查询所有逾期任务"""
    today = date.today()
    results = []

    projects = db.query(Project).filter(Project.status == "active").all()
    for proj in projects:
        phases = db.query(ProjectPhase).filter(
            ProjectPhase.project_id == proj.id
        ).order_by(ProjectPhase.sort_order).all()

        for phase in phases:
            tasks = db.query(ProjectTask).filter(
                ProjectTask.project_phase_id == phase.id,
                ProjectTask.planned_end != None,
                ProjectTask.planned_end < today,
                ProjectTask.status.in_(["pending", "in_progress"]),
            ).all()

            for t in tasks:
                results.append({
                    "project_id": proj.id,
                    "project_name": proj.name,
                    "phase_name": phase.name,
                    "task_id": t.id,
                    "task_name": t.name,
                    "assignee": t.assignee or "",
                    "planned_end": str(t.planned_end),
                    "progress": t.progress or 0,
                    "overdue_days": (today - t.planned_end).days,
                })

    return sorted(results, key=lambda x: x["overdue_days"], reverse=True)


@router.get("/overdue/count")
def get_overdue_count(db: Session = Depends(get_db)):
    """逾期数量（用于前端角标）"""
    today = date.today()
    count = 0

    projects = db.query(Project).filter(Project.status == "active").all()
    for proj in projects:
        phases = db.query(ProjectPhase).filter(
            ProjectPhase.project_id == proj.id
        ).all()
        phase_ids = [p.id for p in phases]
        if not phase_ids:
            continue
        count += db.query(ProjectTask).filter(
            ProjectTask.project_phase_id.in_(phase_ids),
            ProjectTask.planned_end != None,
            ProjectTask.planned_end < today,
            ProjectTask.status.in_(["pending", "in_progress"]),
        ).count()

    return {"count": count}
