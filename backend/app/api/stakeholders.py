from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.project import Project
from app.models.stakeholder import Stakeholder
from pydantic import BaseModel

router = APIRouter(prefix="/api/projects/{project_id}/stakeholders", tags=["stakeholders"])


class StakeholderData(BaseModel):
    group_name: str = ""
    company: str = ""
    name: str = ""
    role: str = ""
    phone: str = ""
    email: str = ""
    notes: str = ""


@router.get("")
def list_stakeholders(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    items = db.query(Stakeholder).filter(Stakeholder.project_id == project_id).order_by(Stakeholder.id).all()
    return {"items": items}


@router.post("", status_code=201)
def create_stakeholder(project_id: int, data: StakeholderData, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    s = Stakeholder(project_id=project_id, **data.model_dump())
    db.add(s)
    db.commit()
    return s


@router.put("/{stakeholder_id}")
def update_stakeholder(project_id: int, stakeholder_id: int, data: StakeholderData, db: Session = Depends(get_db)):
    s = db.query(Stakeholder).filter(Stakeholder.id == stakeholder_id, Stakeholder.project_id == project_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="干系人不存在")
    for k, v in data.model_dump().items():
        setattr(s, k, v)
    db.commit()
    return s


@router.delete("/{stakeholder_id}")
def delete_stakeholder(project_id: int, stakeholder_id: int, db: Session = Depends(get_db)):
    s = db.query(Stakeholder).filter(Stakeholder.id == stakeholder_id, Stakeholder.project_id == project_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="干系人不存在")
    db.delete(s)
    db.commit()
    return {"status": "ok"}
