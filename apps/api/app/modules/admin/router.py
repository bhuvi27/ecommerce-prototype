from typing import Annotated
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from bson import ObjectId
from app.shared.deps import get_admin_user
from app.shared.db.models import User
from app.shared.mongo import get_mongo
from app.shared.storage.s3 import upload_bytes
from app.shared.redis.client import redis_delete
from app.modules.admin.schemas import CategoryCreate, ProductCreate, ProductUpdate
from app.modules.catalog.service import CACHE_CATEGORIES, CACHE_PRODUCTS, _product_doc
from app.modules.catalog.schemas import ProductResponse

router = APIRouter(prefix="/admin", tags=["admin"])


async def _invalidate_catalog_cache():
    r = __import__("app.shared.redis.client", fromlist=["get_redis"]).get_redis()
    keys = await r.keys(f"{CACHE_PRODUCTS}*")
    if keys:
        await r.delete(*keys)
    await redis_delete(CACHE_CATEGORIES)


@router.post("/categories", status_code=201)
async def create_category(body: CategoryCreate, _: Annotated[User, Depends(get_admin_user)]):
    db = get_mongo()
    if await db.categories.find_one({"slug": body.slug}):
        raise HTTPException(400, "Category slug exists")
    result = await db.categories.insert_one(body.model_dump())
    await _invalidate_catalog_cache()
    return {"id": str(result.inserted_id), **body.model_dump()}


@router.post("/products", response_model=ProductResponse, status_code=201)
async def create_product(body: ProductCreate, _: Annotated[User, Depends(get_admin_user)]):
    db = get_mongo()
    cat = await db.categories.find_one({"slug": body.category_slug})
    if not cat:
        raise HTTPException(400, "Category not found")
    if await db.products.find_one({"slug": body.slug}):
        raise HTTPException(400, "Product slug exists")
    doc = {
        **body.model_dump(),
        "category_id": str(cat["_id"]),
        "skus": [s.model_dump() for s in body.skus],
    }
    result = await db.products.insert_one(doc)
    doc["_id"] = result.inserted_id
    await _invalidate_catalog_cache()
    return _product_doc(doc)


@router.patch("/products/{product_id}", response_model=ProductResponse)
async def update_product(product_id: str, body: ProductUpdate, _: Annotated[User, Depends(get_admin_user)]):
    db = get_mongo()
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if "skus" in updates:
        updates["skus"] = [s.model_dump() if hasattr(s, "model_dump") else s for s in updates["skus"]]
    result = await db.products.find_one_and_update(
        {"_id": ObjectId(product_id)}, {"$set": updates}, return_document=True
    )
    if not result:
        raise HTTPException(404, "Product not found")
    await _invalidate_catalog_cache()
    return _product_doc(result)


@router.post("/upload")
async def upload_image(_: Annotated[User, Depends(get_admin_user)], file: UploadFile = File(...)):
    data = await file.read()
    url = upload_bytes(data, file.content_type or "image/jpeg")
    return {"url": url}
