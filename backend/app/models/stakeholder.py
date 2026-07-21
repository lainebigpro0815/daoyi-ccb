from sqlalchemy import Column, Integer, String, ForeignKey
from app.database import Base


class Stakeholder(Base):
    __tablename__ = "stakeholder"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("project.id"), nullable=False)
    group_name = Column(String(50), default="", comment="分组：客户联系人 / 内部联系人")
    company = Column(String(200), default="", comment="公司")
    name = Column(String(100), default="", comment="姓名")
    role = Column(String(100), default="", comment="职位/角色")
    phone = Column(String(50), default="", comment="电话")
    email = Column(String(200), default="", comment="邮箱")
    notes = Column(String(500), default="", comment="关注点/备注")
