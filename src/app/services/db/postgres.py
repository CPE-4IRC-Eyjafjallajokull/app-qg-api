from typing import AsyncIterator, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings
from app.models import Base


class PostgresManager:
    """Async SQLAlchemy engine/session factory helper."""

    def __init__(self, settings: Settings):
        self._dsn = settings.postgres_dsn
        self._engine: Optional[AsyncEngine] = None
        self._sessionmaker: Optional[async_sessionmaker[AsyncSession]] = None

    def engine(self) -> AsyncEngine:
        if not self._engine:
            self._engine = create_async_engine(self._dsn, echo=False, future=True)
            self._sessionmaker = async_sessionmaker(
                self._engine, expire_on_commit=False
            )
        return self._engine

    def sessionmaker(self) -> async_sessionmaker[AsyncSession]:
        if not self._sessionmaker:
            self.engine()
        assert self._sessionmaker is not None
        return self._sessionmaker

    async def get_session(self) -> AsyncIterator[AsyncSession]:
        async with self.sessionmaker()() as session:
            yield session

    async def create_tables(self) -> None:
        """Create all tables defined in models."""
        async with self.engine().begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self) -> None:
        """Drop all tables defined in models."""
        async with self.engine().begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def connect(self) -> None:
        """Verify database connection is working."""
        async with self.engine().connect() as conn:
            await conn.execute(text("SELECT 1"))

    async def close(self) -> None:
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._sessionmaker = None
