from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.product import Product
from app.schemas.product import ProductResponse, ProductList

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=ProductList)
def list_products(db: Session = Depends(get_db)):
    items = db.query(Product).filter(Product.is_active == True).order_by(Product.sort_order).all()
    return ProductList(items=items)
