from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import Settings


class MongoClientManager:
    """Lazy MongoDB client holder."""

    def __init__(self, settings: Settings):
        self._dsn = settings.mongo_dsn
        self._client: Optional[AsyncIOMotorClient] = None

    @property
    def client(self) -> AsyncIOMotorClient:
        if not self._client:
            self._client = AsyncIOMotorClient(self._dsn)
        return self._client

    async def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None
