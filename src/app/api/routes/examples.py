"""
Example routes demonstrating User and Article model usage with SQLAlchemy.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import get_postgres_session
from app.models.article import Article
from app.models.user import User

router = APIRouter(prefix="/examples", tags=["examples"])


# Pydantic schemas for request/response
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    first_name: str | None = None
    last_name: str | None = None


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    first_name: str | None
    last_name: str | None
    is_active: bool
    is_verified: bool

    class Config:
        from_attributes = True


class ArticleCreate(BaseModel):
    title: str
    slug: str
    content: str
    excerpt: str | None = None
    status: str = "draft"


class ArticleResponse(BaseModel):
    id: int
    title: str
    slug: str
    content: str
    excerpt: str | None
    author_id: int
    status: str
    published_at: str | None

    class Config:
        from_attributes = True


class ArticleWithAuthor(ArticleResponse):
    author: UserResponse


# User endpoints
@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate, session: AsyncSession = Depends(get_postgres_session)
):
    """Create a new user."""
    # In production, hash the password properly (e.g., with bcrypt)
    password_hash = f"hashed_{user_data.password}"

    user = User(
        email=user_data.email,
        username=user_data.username,
        password_hash=password_hash,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 10,
    session: AsyncSession = Depends(get_postgres_session),
):
    """List all users with pagination."""
    result = await session.execute(
        select(User).where(User.is_active).offset(skip).limit(limit)
    )
    users = result.scalars().all()
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, session: AsyncSession = Depends(get_postgres_session)):
    """Get a specific user by ID."""
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# Article endpoints
@router.post("/users/{user_id}/articles", response_model=ArticleResponse)
async def create_article(
    user_id: int,
    article_data: ArticleCreate,
    session: AsyncSession = Depends(get_postgres_session),
):
    """Create a new article for a user."""
    # Verify user exists
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    article = Article(
        title=article_data.title,
        slug=article_data.slug,
        content=article_data.content,
        excerpt=article_data.excerpt,
        author_id=user_id,
        status=article_data.status,
    )
    session.add(article)
    await session.commit()
    await session.refresh(article)
    return article


@router.get("/articles", response_model=List[ArticleWithAuthor])
async def list_articles(
    status: str | None = None,
    skip: int = 0,
    limit: int = 10,
    session: AsyncSession = Depends(get_postgres_session),
):
    """List all articles with their authors."""
    query = select(Article).options(selectinload(Article.author))

    if status:
        query = query.where(Article.status == status)

    query = query.offset(skip).limit(limit).order_by(Article.created_at.desc())

    result = await session.execute(query)
    articles = result.scalars().all()
    return articles


@router.get("/articles/{article_id}", response_model=ArticleWithAuthor)
async def get_article(
    article_id: int, session: AsyncSession = Depends(get_postgres_session)
):
    """Get a specific article by ID with author information."""
    result = await session.execute(
        select(Article)
        .options(selectinload(Article.author))
        .where(Article.id == article_id)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.patch("/articles/{article_id}/publish")
async def publish_article(
    article_id: int, session: AsyncSession = Depends(get_postgres_session)
):
    """Publish an article."""
    result = await session.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    article.publish()
    await session.commit()
    return {"status": "published", "published_at": article.published_at}


@router.get("/users/{user_id}/articles", response_model=List[ArticleResponse])
async def get_user_articles(
    user_id: int, session: AsyncSession = Depends(get_postgres_session)
):
    """Get all articles by a specific user."""
    result = await session.execute(
        select(Article)
        .where(Article.author_id == user_id)
        .order_by(Article.created_at.desc())
    )
    articles = result.scalars().all()
    return articles
