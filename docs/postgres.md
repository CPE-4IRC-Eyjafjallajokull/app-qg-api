# PostgreSQL (SQLAlchemy async) quick use

## Models

SQLAlchemy ORM models are defined in `src/app/models/`:

- `user.py` - User model with authentication fields
- `article.py` - Article model with foreign key to User

### Example Model Usage

```python
from app.models.user import User
from app.models.article import Article
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# Create a user
user = User(
    email="user@example.com",
    username="johndoe",
    password_hash="hashed_password"
)
session.add(user)
await session.commit()

# Query users
result = await session.execute(select(User).where(User.is_active == True))
users = result.scalars().all()

# Create an article
article = Article(
    title="My Article",
    slug="my-article",
    content="Content here...",
    author_id=user.id
)
session.add(article)
await session.commit()

# Query with relationships
result = await session.execute(
    select(Article).options(selectinload(Article.author))
)
articles = result.scalars().all()
```

## Database Initialization

Create all tables:

```bash
python -m app.scripts.init_db
```

Drop all tables (careful!):

```bash
python -m app.scripts.init_db drop
```

## Using in Routes

Use the shared `AsyncSession` from `get_postgres_session`.

```python
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_postgres_session
from app.models.user import User

router = APIRouter()


@router.get("/users")
async def list_users(session: AsyncSession = Depends(get_postgres_session)):
    result = await session.execute(select(User).limit(10))
    users = result.scalars().all()
    return [{"id": u.id, "email": u.email, "username": u.username} for u in users]


@router.post("/users")
async def create_user(
    email: str,
    username: str,
    password: str,
    session: AsyncSession = Depends(get_postgres_session)
):
    user = User(email=email, username=username, password_hash=f"hashed_{password}")
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return {"id": user.id, "username": user.username}
```

See `src/app/api/routes/examples.py` for complete CRUD examples.
