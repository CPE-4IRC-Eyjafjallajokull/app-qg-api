from typing import AsyncIterator

from fastapi import Request
from aio_pika.abc import AbstractRobustConnection
from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.db.mongo import MongoClientManager
from app.services.db.postgres import PostgresManager
from app.services.messaging.rabbitmq import RabbitMQManager


def get_mongo_client(request: Request) -> AsyncIOMotorClient:
    manager: MongoClientManager = request.app.state.mongo
    return manager.client


async def get_postgres_session(request: Request) -> AsyncIterator[AsyncSession]:
    manager: PostgresManager = request.app.state.postgres
    async for session in manager.get_session():
        yield session


async def get_rabbitmq_connection(request: Request) -> AbstractRobustConnection:
    manager: RabbitMQManager = request.app.state.rabbitmq
    return await manager.get_connection()
