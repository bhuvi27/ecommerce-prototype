from fastapi import APIRouter, HTTPException, Query
from app.modules.catalog import service
from app.modules.catalog.schemas import CategoryResponse, ProductListResponse, ProductResponse

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/categories", response_model=list[CategoryResponse])
async def categories():
    return await service.list_categories()


@router.get("/products", response_model=ProductListResponse)
async def products(
    category: str | None = Query(None),
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    return await service.list_products(category_slug=category, cursor=cursor, limit=limit)


@router.get("/products/{slug}", response_model=ProductResponse)
async def product_detail(slug: str):
    p = await service.get_product_by_slug(slug)
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    return p
