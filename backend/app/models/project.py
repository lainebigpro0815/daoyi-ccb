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
