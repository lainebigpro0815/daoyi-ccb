from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.project import Project
from app.models.tracking import Risk, Issue
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/projects/{project_id}", tags=["tracking"])


# ===== Risk =====
class RiskData(BaseModel):
    level: str = "中"
    category: str = ""
    description: str = ""
    impact: str = ""
    probability: str = ""
    mitigation: str = ""
    owner: str = ""
    status: str = "open"


@router.get("/risks")
def list_risks(project_id: int, db: Session = Depends(get_db)):
    return {"items": db.query(Risk).filter(Risk.project_id == project_id).order_by(Risk.id).all()}


@router.post("/risks", status_code=201)
def create_risk(project_id: int, data: RiskData, db: Session = Depends(get_db)):
    r = Risk(project_id=project_id, created_at=date.today(), **data.model_dump())
    db.add(r); db.commit(); db.refresh(r); return r


@router.put("/risks/{risk_id}")
def update_risk(project_id: int, risk_id: int, data: RiskData, db: Session = Depends(get_db)):
    r = db.query(Risk).filter(Risk.id == risk_id, Risk.project_id == project_id).first()
    if not r: raise HTTPException(404, "不存在")
    for k, v in data.model_dump().items(): setattr(r, k, v)
    db.commit(); return r


@router.delete("/risks/{risk_id}")
def delete_risk(project_id: int, risk_id: int, db: Session = Depends(get_db)):
    r = db.query(Risk).filter(Risk.id == risk_id, Risk.project_id == project_id).first()
    if not r: raise HTTPException(404, "不存在")
    db.delete(r); db.commit(); return {"ok": True}


# ===== Issue =====
class IssueData(BaseModel):
    severity: str = "一般"
    module: str = ""
    description: str = ""
    status: str = "open"
    priority: str = "中"
    assignee: str = ""
    resolution: str = ""


@router.get("/issues")
def list_issues(project_id: int, db: Session = Depends(get_db)):
    return {"items": db.query(Issue).filter(Issue.project_id == project_id).order_by(Issue.id).all()}


@router.post("/issues", status_code=201)
def create_issue(project_id: int, data: IssueData, db: Session = Depends(get_db)):
    i = Issue(project_id=project_id, created_at=date.today(), **data.model_dump())
    db.add(i); db.commit(); db.refresh(i); return i


@router.put("/issues/{issue_id}")
def update_issue(project_id: int, issue_id: int, data: IssueData, db: Session = Depends(get_db)):
    i = db.query(Issue).filter(Issue.id == issue_id, Issue.project_id == project_id).first()
    if not i: raise HTTPException(404, "不存在")
    for k, v in data.model_dump().items(): setattr(i, k, v)
    if data.status == "resolved" and not i.resolved_at:
        i.resolved_at = date.today()
    db.commit(); return i


@router.delete("/issues/{issue_id}")
def delete_issue(project_id: int, issue_id: int, db: Session = Depends(get_db)):
    i = db.query(Issue).filter(Issue.id == issue_id, Issue.project_id == project_id).first()
    if not i: raise HTTPException(404, "不存在")
    db.delete(i); db.commit(); return {"ok": True}
