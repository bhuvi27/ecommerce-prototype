import json
from typing import Any
import redis.asyncio as redis
from app.config import get_settings

_settings = get_settings()
_pool: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _pool
    if _pool is None:
        _pool = redis.from_url(_settings.redis_url, decode_responses=True)
    return _pool


async def redis_get(key: str) -> Any | None:
    r = get_redis()
    val = await r.get(key)
    return json.loads(val) if val else None


async def redis_set(key: str, value: Any, ttl: int | None = None) -> None:
    r = get_redis()
    data = json.dumps(value, default=str)
    if ttl:
        await r.setex(key, ttl, data)
    else:
        await r.set(key, data)


async def redis_delete(key: str) -> None:
    await get_redis().delete(key)


async def redis_ping() -> bool:
    try:
        return await get_redis().ping()
    except Exception:
        return False
