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


class StakeholderItem(BaseModel):
    id: int
    group_name: str = ""
    company: str = ""
    name: str = ""
    role: str = ""
    phone: str = ""
    email: str = ""
    notes: str = ""

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
    stakeholders: list[StakeholderItem] = []

    class Config:
        from_attributes = True


class ProjectCreate(BaseModel):
    name: str
    customer_name: str = ""
    stage: str = "presale"
    start_date: date
    product_ids: list[int]
    template_id: int | None = None


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


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    customer_name: Optional[str] = None
    stage: Optional[str] = None
    start_date: Optional[date] = None
    status: Optional[str] = None


class TaskUpdate(BaseModel):
    status: Optional[str] = None
    progress: Optional[int] = None
    assignee: Optional[str] = None
    name: Optional[str] = None
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    notes: Optional[str] = None
