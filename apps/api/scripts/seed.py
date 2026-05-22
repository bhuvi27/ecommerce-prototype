"""Run: cd apps/api && python -m scripts.seed"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from app.config import get_settings
from app.shared.db.session import async_session_factory, engine
from app.shared.db.base import Base
from app.shared.db.models import User, UserRole
from app.shared.security import hash_password
from app.shared.mongo import get_mongo
from app.shared.redis.client import redis_delete
from app.modules.catalog.service import CACHE_CATEGORIES, CACHE_PRODUCTS


CATEGORIES = [
    {"slug": "oil", "name": "Oils", "description": "Natural beauty oils"},
    {"slug": "facewash", "name": "Face Wash", "description": "Gentle cleansers"},
    {"slug": "cream", "name": "Creams", "description": "Moisturizing creams"},
]

PRODUCTS = [
    {
        "slug": "coconut-oil",
        "name": "Pure Coconut Oil",
        "description": "Cold-pressed virgin coconut oil for hair and skin.",
        "category_slug": "oil",
        "status": "active",
        "image_url": "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=400",
        "skus": [{"id": "default", "label": "200ml", "price": 29900, "currency": "INR"}],
        "attributes": {"type": "oil", "volume": "200ml"},
    },
    {
        "slug": "almond-oil",
        "name": "Sweet Almond Oil",
        "description": "Nourishing almond oil for soft skin.",
        "category_slug": "oil",
        "status": "active",
        "image_url": "https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=400",
        "skus": [{"id": "default", "label": "100ml", "price": 44900, "currency": "INR"}],
        "attributes": {"type": "oil", "volume": "100ml"},
    },
    {
        "slug": "neem-facewash",
        "name": "Neem Face Wash",
        "description": "Antibacterial neem facewash for clear skin.",
        "category_slug": "facewash",
        "status": "active",
        "image_url": "https://images.unsplash.com/photo-1556228578-0d85b1a4d571?w=400",
        "skus": [{"id": "default", "label": "150ml", "price": 19900, "currency": "INR"}],
        "attributes": {"type": "facewash"},
    },
    {
        "slug": "boroplus-cream",
        "name": "Boroplus Antiseptic Cream",
        "description": "Classic antiseptic cream for dry skin.",
        "category_slug": "cream",
        "status": "active",
        "image_url": "https://images.unsplash.com/photo-1620916566398-39f1149ab7be?w=400",
        "skus": [{"id": "default", "label": "40ml", "price": 8900, "currency": "INR"}],
        "attributes": {"type": "cream"},
    },
    {
        "slug": "moisturizing-cream",
        "name": "Daily Moisturizing Cream",
        "description": "Lightweight daily moisturizer for all skin types.",
        "category_slug": "cream",
        "status": "active",
        "image_url": "https://images.unsplash.com/photo-1611934551095-5bf920691f47?w=400",
        "skus": [{"id": "default", "label": "50ml", "price": 34900, "currency": "INR"}],
        "attributes": {"type": "cream"},
    },
]


async def seed():
    settings = get_settings()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    db = get_mongo()
    await db.categories.delete_many({})
    await db.products.delete_many({})

    cat_ids = {}
    for c in CATEGORIES:
        r = await db.categories.insert_one(c)
        cat_ids[c["slug"]] = r.inserted_id

    for p in PRODUCTS:
        doc = {**p, "category_id": str(cat_ids[p["category_slug"]])}
        await db.products.insert_one(doc)

    # Skip Redis cache clear if Redis is unavailable
    try:
        await redis_delete(CACHE_CATEGORIES)
    except Exception as e:
        print(f"Warning: Could not clear Redis cache: {e}")

    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.email == settings.admin_email))
        if not result.scalar_one_or_none():
            admin = User(
                email=settings.admin_email,
                password_hash=hash_password(settings.admin_password),
                name="Admin",
                role=UserRole.admin,
            )
            session.add(admin)
            await session.commit()
            print(f"Admin created: {settings.admin_email} / {settings.admin_password}")
        else:
            print("Admin already exists")

    print(f"Seeded {len(CATEGORIES)} categories and {len(PRODUCTS)} products")


if __name__ == "__main__":
    asyncio.run(seed())
