from typing import AsyncIterator

from aio_pika.abc import AbstractRobustConnection
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.db.postgres import PostgresManager
from app.services.events import SSEManager
from app.services.messaging.rabbitmq import RabbitMQManager


async def get_postgres_session(request: Request) -> AsyncIterator[AsyncSession]:
    manager: PostgresManager = request.app.state.postgres
    async for session in manager.get_session():
        yield session


async def get_rabbitmq_connection(request: Request) -> AbstractRobustConnection:
    manager: RabbitMQManager = request.app.state.rabbitmq
    return await manager.get_connection()


def get_rabbitmq_manager(request: Request) -> RabbitMQManager:
    """Get the RabbitMQ manager for publishing/consuming messages."""
    return request.app.state.rabbitmq


def get_sse_manager(request: Request) -> SSEManager:
    """Get the SSE manager for broadcasting events to connected clients."""
    return request.app.state.sse
