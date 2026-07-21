from sqlalchemy import Column, Integer, String, Text, Boolean
from app.database import Base


class Product(Base):
    __tablename__ = "product"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="产品名")
    code = Column(String(50), unique=True, nullable=False, comment="唯一编码")
    description = Column(Text, default="", comment="产品说明")
    sort_order = Column(Integer, default=0, comment="排序")
    is_active = Column(Boolean, default=True, comment="是否启用")
