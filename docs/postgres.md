# PostgreSQL (SQLAlchemy async) quick use

Use the shared `AsyncSession` from `get_postgres_session`.

```python
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_postgres_session

router = APIRouter()


@router.get("/users")
async def list_users(session: AsyncSession = Depends(get_postgres_session)):
    result = await session.execute(text("SELECT id, email FROM users LIMIT 10"))
    return [dict(row) for row in result.mappings()]


@router.post("/users")
async def create_user(email: str, session: AsyncSession = Depends(get_postgres_session)):
    await session.execute(text("INSERT INTO users (email) VALUES (:email)"), {"email": email})
    await session.commit()
    return {"status": "created"}
```
