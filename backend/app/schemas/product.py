from pydantic import BaseModel
from typing import Optional


class ProductBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = ""
    sort_order: int = 0


class ProductResponse(ProductBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True


class ProductList(BaseModel):
    items: list[ProductResponse]
