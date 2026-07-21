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
