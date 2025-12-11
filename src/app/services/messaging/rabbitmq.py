import asyncio
from typing import Any, Callable, Coroutine, Optional

import aio_pika
from aio_pika.abc import (
    AbstractIncomingMessage,
    AbstractRobustChannel,
    AbstractRobustConnection,
    AbstractRobustQueue,
)

from app.core.config import RabbitMQSettings
from app.core.logging import get_logger

log = get_logger(__name__)


class RabbitMQManager:
    """
    Robust RabbitMQ connection helper with consumer support.

    Designed for async applications with support for:
    - Robust connection with auto-reconnect
    - Channel pooling
    - Message consumption with callbacks
    - Integration with SSE for real-time event broadcasting
    """

    def __init__(self, settings: RabbitMQSettings):
        self._dsn = settings.dsn
        self._connect_timeout = settings.connect_timeout_seconds
        self._connection: Optional[AbstractRobustConnection] = None
        self._channel: Optional[AbstractRobustChannel] = None
        self._consumers: dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()

    async def get_connection(self) -> AbstractRobustConnection:
        """Get or create a robust RabbitMQ connection."""
        if self._connection and not self._connection.is_closed:
            return self._connection

        async with self._lock:
            if not self._connection or self._connection.is_closed:
                self._connection = await aio_pika.connect_robust(
                    self._dsn, timeout=self._connect_timeout
                )
                log.info("rabbitmq.connection.established")
        return self._connection

    async def get_channel(self) -> AbstractRobustChannel:
        """Get or create a channel from the connection."""
        if self._channel and not self._channel.is_closed:
            return self._channel

        connection = await self.get_connection()
        async with self._lock:
            if not self._channel or self._channel.is_closed:
                self._channel = await connection.channel()
                log.info("rabbitmq.channel.opened")
        return self._channel

    async def connect(self) -> None:
        """Establish and verify RabbitMQ connection."""
        await self.get_connection()

    async def declare_queue(
        self,
        queue_name: str,
        durable: bool = True,
        auto_delete: bool = False,
        channel: AbstractRobustChannel | None = None,
    ) -> AbstractRobustQueue:
        """Declare a queue and return it."""
        channel = channel or await self.get_channel()
        queue = await channel.declare_queue(
            queue_name,
            durable=durable,
            auto_delete=auto_delete,
        )
        log.info("rabbitmq.queue.declared", queue=queue_name)
        return queue

    async def publish(
        self,
        queue_name: str,
        message: bytes,
        content_type: str = "application/json",
        channel: AbstractRobustChannel | None = None,
    ) -> None:
        """Publish a message to a queue."""
        channel = channel or await self.get_channel()
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=message,
                content_type=content_type,
            ),
            routing_key=queue_name,
        )
        log.debug("rabbitmq.message.published", queue=queue_name)

    async def consume(
        self,
        queue_name: str,
        callback: Callable[[AbstractIncomingMessage], Coroutine[Any, Any, None]],
        prefetch_count: int = 10,
    ) -> None:
        """
        Start consuming messages from a queue.

        Args:
            queue_name: The queue to consume from
            callback: Async callback function to handle messages
            prefetch_count: Number of messages to prefetch
        """
        channel = await self.get_channel()
        await channel.set_qos(prefetch_count=prefetch_count)

        queue = await self.declare_queue(queue_name, channel=channel)

        async def _consumer_wrapper():
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    try:
                        await callback(message)
                        await message.ack()
                    except Exception as e:
                        log.error(
                            "rabbitmq.message.error", error=str(e), queue=queue_name
                        )
                        await message.nack(requeue=True)

        task = asyncio.create_task(_consumer_wrapper())
        self._consumers[queue_name] = task
        log.info("rabbitmq.consumer.started", queue=queue_name)

    async def enqueue(
        self,
        queue_name: str,
        message: bytes,
        content_type: str = "application/json",
        timeout: float | None = None,
    ) -> None:
        """Declare the queue then publish, with an optional timeout."""
        timeout = timeout or self._connect_timeout

        async def _do():
            channel = await self.get_channel()
            await self.declare_queue(queue_name, channel=channel)
            await self.publish(
                queue_name,
                message,
                content_type=content_type,
                channel=channel,
            )

        await asyncio.wait_for(_do(), timeout=timeout)

    async def stop_consumer(self, queue_name: str) -> None:
        """Stop a specific consumer."""
        if queue_name in self._consumers:
            self._consumers[queue_name].cancel()
            try:
                await self._consumers[queue_name]
            except asyncio.CancelledError:
                pass
            del self._consumers[queue_name]
            log.info("rabbitmq.consumer.stopped", queue=queue_name)

    async def close(self) -> None:
        """Close all consumers, channels, and the connection."""
        # Stop all consumers
        for queue_name in list(self._consumers.keys()):
            await self.stop_consumer(queue_name)

        # Close channel
        if self._channel and not self._channel.is_closed:
            await self._channel.close()
            self._channel = None

        # Close connection
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
            self._connection = None

        log.info("rabbitmq.connection.closed")
