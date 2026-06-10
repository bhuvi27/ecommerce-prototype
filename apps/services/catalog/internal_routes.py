from fastapi import APIRouter, HTTPException

from app.modules.catalog import service
from app.modules.catalog.schemas import ProductResponse

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/products/id/{product_id}", response_model=ProductResponse)
async def product_by_id(product_id: str):
    product = await service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
