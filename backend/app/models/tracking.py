from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey
from app.database import Base


class Risk(Base):
    __tablename__ = "risk"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("project.id"), nullable=False)
    level = Column(String(20), default="中", comment="高/中/低")
    category = Column(String(100), default="", comment="风险类别")
    description = Column(Text, default="", comment="风险描述")
    impact = Column(String(50), default="", comment="影响程度")
    probability = Column(String(20), default="", comment="概率")
    mitigation = Column(Text, default="", comment="应对措施")
    owner = Column(String(100), default="", comment="负责人")
    status = Column(String(20), default="open", comment="open / closed")
    created_at = Column(Date, comment="识别日期")


class Issue(Base):
    __tablename__ = "issue"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("project.id"), nullable=False)
    severity = Column(String(20), default="中", comment="严重/一般/轻微")
    module = Column(String(100), default="", comment="所属模块")
    description = Column(Text, default="", comment="问题描述")
    status = Column(String(20), default="open", comment="open / in_progress / resolved / closed")
    priority = Column(String(20), default="中", comment="高/中/低")
    assignee = Column(String(100), default="", comment="处理人")
    resolution = Column(Text, default="", comment="解决方案")
    created_at = Column(Date, comment="发现日期")
    resolved_at = Column(Date, comment="解决日期")


class Milestone(Base):
    __tablename__ = "milestone"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("project.id"), nullable=False)
    name = Column(String(200), default="", comment="里程碑名称")
    planned_date = Column(String(20), default="", comment="计划日期")
    actual_date = Column(String(20), default="", comment="实际日期")
    status = Column(String(20), default="pending", comment="pending/completed/delayed")
    description = Column(Text, default="", comment="说明")


class AcceptanceItem(Base):
    __tablename__ = "acceptance_item"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("project.id"), nullable=False)
    item = Column(String(200), default="", comment="验收项")
    standard = Column(Text, default="", comment="验收标准")
    status = Column(String(20), default="pending", comment="pending/passed/failed")
    result = Column(Text, default="", comment="验收结果")
    remark = Column(Text, default="", comment="备注")


class TrainingItem(Base):
    __tablename__ = "training_item"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("project.id"), nullable=False)
    content = Column(String(200), default="", comment="培训内容")
    target = Column(String(200), default="", comment="培训对象")
    planned_date = Column(String(20), default="", comment="计划日期")
    actual_date = Column(String(20), default="", comment="实际日期")
    status = Column(String(20), default="pending", comment="pending/completed")
    remark = Column(Text, default="", comment="备注")
