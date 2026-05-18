from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import get_settings

_client: AsyncIOMotorClient | None = None


def get_mongo() -> AsyncIOMotorDatabase:
    global _client
    s = get_settings()
    if _client is None:
        _client = AsyncIOMotorClient(s.mongodb_uri)
    return _client[s.mongodb_db]


async def mongo_ping() -> bool:
    try:
        await get_mongo().command("ping")
        return True
    except Exception:
        return False
