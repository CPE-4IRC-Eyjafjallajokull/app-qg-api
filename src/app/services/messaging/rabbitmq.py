from typing import Optional

import aio_pika
from aio_pika.abc import AbstractRobustConnection

from app.core.config import Settings


class RabbitMQManager:
    """Robust RabbitMQ connection helper."""

    def __init__(self, settings: Settings):
        self._dsn = settings.rabbitmq_dsn
        self._connection: Optional[AbstractRobustConnection] = None

    async def get_connection(self) -> AbstractRobustConnection:
        if not self._connection:
            self._connection = await aio_pika.connect_robust(self._dsn)
        return self._connection

    async def close(self) -> None:
        if self._connection:
            await self._connection.close()
            self._connection = None
