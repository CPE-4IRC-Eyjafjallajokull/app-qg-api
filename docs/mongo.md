# MongoDB (motor) quick use

Leverage the shared `AsyncIOMotorClient` via `get_mongo_client`.

```python
from bson import ObjectId
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.api.dependencies import get_mongo_client

router = APIRouter()


def get_db(client: AsyncIOMotorClient = Depends(get_mongo_client)) -> AsyncIOMotorDatabase:
    return client.get_default_database()


@router.get("/items/{item_id}")
async def read_item(item_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    doc = await db.items.find_one({"_id": ObjectId(item_id)})
    return doc or {}


@router.post("/items")
async def create_item(payload: dict, db: AsyncIOMotorDatabase = Depends(get_db)):
    result = await db.items.insert_one(payload)
    return {"id": str(result.inserted_id)}
```
