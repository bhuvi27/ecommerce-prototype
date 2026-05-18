from bson import ObjectId
from app.config import get_settings
from app.shared.mongo import get_mongo
from app.shared.redis.client import redis_get, redis_set
from app.modules.catalog.schemas import CategoryResponse, ProductListResponse, ProductResponse, ProductSkuResponse

CACHE_PRODUCTS = "catalog:products:active"
CACHE_CATEGORIES = "catalog:categories"


def _product_doc(doc: dict) -> ProductResponse:
    skus = [ProductSkuResponse(**s) for s in doc.get("skus", [])]
    return ProductResponse(
        id=str(doc["_id"]),
        slug=doc["slug"],
        name=doc["name"],
        description=doc.get("description"),
        category_id=doc["category_id"],
        category_slug=doc.get("category_slug", ""),
        status=doc["status"],
        image_url=doc.get("image_url"),
        skus=skus,
        attributes=doc.get("attributes", {}),
    )


async def list_categories() -> list[CategoryResponse]:
    cached = await redis_get(CACHE_CATEGORIES)
    if cached:
        return [CategoryResponse(**c) for c in cached]
    db = get_mongo()
    cursor = db.categories.find({}).sort("name", 1)
    items = [
        CategoryResponse(id=str(c["_id"]), slug=c["slug"], name=c["name"], description=c.get("description"))
        async for c in cursor
    ]
    await redis_set(CACHE_CATEGORIES, [i.model_dump() for i in items], get_settings().catalog_cache_ttl)
    return items


async def list_products(category_slug: str | None = None, cursor: str | None = None, limit: int = 20) -> ProductListResponse:
    cache_key = f"{CACHE_PRODUCTS}:{category_slug or 'all'}:{cursor or 'start'}:{limit}"
    cached = await redis_get(cache_key)
    if cached:
        return ProductListResponse(**cached)

    db = get_mongo()
    query: dict = {"status": "active"}
    if category_slug:
        query["category_slug"] = category_slug
    if cursor:
        query["_id"] = {"$gt": ObjectId(cursor)}

    docs = await db.products.find(query).sort("_id", 1).limit(limit + 1).to_list(limit + 1)
    has_more = len(docs) > limit
    if has_more:
        docs = docs[:limit]
    items = [_product_doc(d) for d in docs]
    next_cursor = str(docs[-1]["_id"]) if has_more and docs else None
    result = ProductListResponse(items=items, next_cursor=next_cursor)
    await redis_set(cache_key, result.model_dump(), get_settings().catalog_cache_ttl)
    return result


async def get_product_by_slug(slug: str) -> ProductResponse | None:
    db = get_mongo()
    doc = await db.products.find_one({"slug": slug, "status": "active"})
    return _product_doc(doc) if doc else None


async def get_product_by_id(product_id: str) -> ProductResponse | None:
    db = get_mongo()
    try:
        doc = await db.products.find_one({"_id": ObjectId(product_id), "status": "active"})
    except Exception:
        return None
    return _product_doc(doc) if doc else None
