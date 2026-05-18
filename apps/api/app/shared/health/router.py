from fastapi import APIRouter
from sqlalchemy import text
from app.shared.db.session import engine
from app.shared.mongo import mongo_ping
from app.shared.redis.client import redis_ping

router = APIRouter(tags=["health"])


@router.get("/health/live")
async def liveness():
    return {"status": "ok"}


@router.get("/health/ready")
async def readiness():
    checks = {}
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception as e:
        checks["postgres"] = f"fail: {e}"

    checks["mongo"] = "ok" if await mongo_ping() else "fail"
    checks["redis"] = "ok" if await redis_ping() else "fail"

    ready = all(v == "ok" for v in checks.values())
    return {"status": "ready" if ready else "degraded", "checks": checks}
