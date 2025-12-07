from typing import AsyncIterator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings


class PostgresManager:
    """Async SQLAlchemy engine/session factory helper."""

    def __init__(self, settings: Settings):
        self._dsn = settings.postgres_dsn
        self._echo = settings.debug
        self._engine: Optional[AsyncEngine] = None
        self._sessionmaker: Optional[async_sessionmaker[AsyncSession]] = None

    def engine(self) -> AsyncEngine:
        if not self._engine:
            self._engine = create_async_engine(self._dsn, echo=self._echo, future=True)
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

    async def close(self) -> None:
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._sessionmaker = None
