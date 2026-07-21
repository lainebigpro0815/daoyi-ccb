from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload
from app.database import get_db
from app.models.product import Product
from app.models.template import ProcessTemplate, PhaseDefinition
from app.schemas.template import ProcessTemplateResponse

router = APIRouter(prefix="/api/products", tags=["templates"])


@router.get("/{product_id}/template", response_model=ProcessTemplateResponse)
def get_product_template(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    template = db.query(ProcessTemplate).options(
        selectinload(ProcessTemplate.phases).selectinload(PhaseDefinition.tasks)
    ).filter(
        ProcessTemplate.product_id == product_id,
        ProcessTemplate.is_active == True
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="该产品暂无模板")
    return template
