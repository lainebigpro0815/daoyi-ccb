from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.project import Project
from pydantic import BaseModel


class MilestoneData(BaseModel):
    name: str = ""
    planned_date: str = ""
    actual_date: str = ""
    status: str = "pending"
    description: str = ""


class AcceptanceItemData(BaseModel):
    item: str = ""
    standard: str = ""
    status: str = "pending"
    result: str = ""
    remark: str = ""


router = APIRouter(prefix="/api/projects/{project_id}", tags=["tracking"])


# ===== Milestones =====
@router.get("/milestones")
def list_milestones(project_id: int, db: Session = Depends(get_db)):
    from app.models.tracking import Milestone
    return {"items": db.query(Milestone).filter(Milestone.project_id == project_id).order_by(Milestone.id).all()}


@router.post("/milestones", status_code=201)
def create_milestone(project_id: int, data: MilestoneData, db: Session = Depends(get_db)):
    from app.models.tracking import Milestone
    m = Milestone(project_id=project_id, **data.model_dump())
    db.add(m); db.commit(); db.refresh(m); return m


@router.put("/milestones/{mid}")
def update_milestone(project_id: int, mid: int, data: MilestoneData, db: Session = Depends(get_db)):
    from app.models.tracking import Milestone
    m = db.query(Milestone).filter(Milestone.id == mid, Milestone.project_id == project_id).first()
    if not m: raise HTTPException(404)
    for k, v in data.model_dump().items(): setattr(m, k, v)
    db.commit(); return m


@router.delete("/milestones/{mid}")
def delete_milestone(project_id: int, mid: int, db: Session = Depends(get_db)):
    from app.models.tracking import Milestone
    m = db.query(Milestone).filter(Milestone.id == mid, Milestone.project_id == project_id).first()
    if not m: raise HTTPException(404)
    db.delete(m); db.commit(); return {"ok": True}


# ===== Acceptance =====
@router.get("/acceptance")
def list_acceptance(project_id: int, db: Session = Depends(get_db)):
    from app.models.tracking import AcceptanceItem
    return {"items": db.query(AcceptanceItem).filter(AcceptanceItem.project_id == project_id).order_by(AcceptanceItem.id).all()}


@router.post("/acceptance", status_code=201)
def create_acceptance(project_id: int, data: AcceptanceItemData, db: Session = Depends(get_db)):
    from app.models.tracking import AcceptanceItem
    a = AcceptanceItem(project_id=project_id, **data.model_dump())
    db.add(a); db.commit(); db.refresh(a); return a


@router.put("/acceptance/{aid}")
def update_acceptance(project_id: int, aid: int, data: AcceptanceItemData, db: Session = Depends(get_db)):
    from app.models.tracking import AcceptanceItem
    a = db.query(AcceptanceItem).filter(AcceptanceItem.id == aid, AcceptanceItem.project_id == project_id).first()
    if not a: raise HTTPException(404)
    for k, v in data.model_dump().items(): setattr(a, k, v)
    db.commit(); return a


@router.delete("/acceptance/{aid}")
def delete_acceptance(project_id: int, aid: int, db: Session = Depends(get_db)):
    from app.models.tracking import AcceptanceItem
    a = db.query(AcceptanceItem).filter(AcceptanceItem.id == aid, AcceptanceItem.project_id == project_id).first()
    if not a: raise HTTPException(404)
    db.delete(a); db.commit(); return {"ok": True}


class TrainingData(BaseModel):
    content: str = ""
    target: str = ""
    planned_date: str = ""
    actual_date: str = ""
    status: str = "pending"
    remark: str = ""


@router.get("/training")
def list_training(project_id: int, db: Session = Depends(get_db)):
    from app.models.tracking import TrainingItem
    return {"items": db.query(TrainingItem).filter(TrainingItem.project_id == project_id).order_by(TrainingItem.id).all()}


@router.post("/training", status_code=201)
def create_training(project_id: int, data: TrainingData, db: Session = Depends(get_db)):
    from app.models.tracking import TrainingItem
    t = TrainingItem(project_id=project_id, **data.model_dump())
    db.add(t); db.commit(); db.refresh(t); return t


@router.put("/training/{tid}")
def update_training(project_id: int, tid: int, data: TrainingData, db: Session = Depends(get_db)):
    from app.models.tracking import TrainingItem
    t = db.query(TrainingItem).filter(TrainingItem.id == tid, TrainingItem.project_id == project_id).first()
    if not t: raise HTTPException(404)
    for k, v in data.model_dump().items(): setattr(t, k, v)
    db.commit(); return t


@router.delete("/training/{tid}")
def delete_training(project_id: int, tid: int, db: Session = Depends(get_db)):
    from app.models.tracking import TrainingItem
    t = db.query(TrainingItem).filter(TrainingItem.id == tid, TrainingItem.project_id == project_id).first()
    if not t: raise HTTPException(404)
    db.delete(t); db.commit(); return {"ok": True}

