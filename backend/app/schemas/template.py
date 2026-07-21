from pydantic import BaseModel
from typing import Optional


class TaskDefinitionResponse(BaseModel):
    id: int
    task_number: str
    name: str
    guide: Optional[str] = ""
    deliverable: Optional[str] = ""
    vendor_role: Optional[str] = ""
    customer_role: Optional[str] = ""
    estimated_days: float
    sort_order: int

    class Config:
        from_attributes = True


class PhaseDefinitionResponse(BaseModel):
    id: int
    phase_number: int
    name: str
    description: Optional[str] = ""
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
