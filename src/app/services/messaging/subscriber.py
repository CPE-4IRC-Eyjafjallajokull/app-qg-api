from __future__ import annotations

import json
from dataclasses import dataclass
from json import JSONDecodeError
from typing import TYPE_CHECKING, Any, Awaitable, Callable

from aio_pika.abc import AbstractIncomingMessage

from app.core.logging import get_logger

if TYPE_CHECKING:
    from app.services.messaging.queues import Queue
    from app.services.messaging.rabbitmq import RabbitMQManager

log = get_logger(__name__)


@dataclass
class QueueEvent:
    """Standardized message structure consumed from RabbitMQ."""

    event: str
    payload: Any
    queue: str
    raw: dict[str, Any]


MessageHandler = Callable[[QueueEvent], Awaitable[None]]


class RabbitMQSubscriptionService:
    """Consume one or more queues and dispatch messages by `event` field."""

    def __init__(
        self,
        rabbitmq: RabbitMQManager,
        queues: list[Queue] | tuple[Queue, ...],
        prefetch_count: int = 10,
    ):
        self._rabbitmq = rabbitmq
        self._queues = tuple(queues)
        self._prefetch_count = prefetch_count
        self._handlers: dict[str, MessageHandler] = {}
        self._started = False

    def on(self, event: str, handler: MessageHandler) -> None:
        """
        Register a handler for a given event.

        Child classes can call this to subscribe to events they care about.
        """
        event_key = str(event)
        if event_key in self._handlers:
            raise ValueError(f"Handler already registered for event '{event}'")
        self._handlers[event_key] = handler

    async def start(self) -> None:
        """Start consuming the configured queue (idempotent)."""
        if self._started:
            return

        for queue_name in self._queues:
            await self._rabbitmq.consume(
                queue_name,
                lambda message, q=queue_name: self._on_message(q, message),
                prefetch_count=self._prefetch_count,
            )

        self._started = True
        log.info(
            "rabbitmq.subscriptions.started",
            queues=list(self._queues),
            events=sorted(self._handlers.keys()),
        )

    async def stop(self) -> None:
        """Stop consuming the queue (idempotent)."""
        if not self._started:
            return

        for queue_name in self._queues:
            await self._rabbitmq.stop_consumer(queue_name)

        self._started = False
        log.info("rabbitmq.subscriptions.stopped", queues=list(self._queues))

    async def _on_message(
        self, queue_name: "Queue", message: AbstractIncomingMessage
    ) -> None:
        parsed = self._parse_message(queue_name, message)
        if not parsed:
            return

        handler = self._handlers.get(parsed.event)
        if not handler:
            log.warning(
                "rabbitmq.event.unhandled",
                queue=queue_name.queue,
                event_name=parsed.event,
            )
            return

        await handler(parsed)

    def _parse_message(
        self, queue_name: "Queue", message: AbstractIncomingMessage
    ) -> QueueEvent | None:
        try:
            content = json.loads(message.body.decode())
        except JSONDecodeError:
            body_preview = message.body[:200].decode(errors="replace")
            log.warning(
                "rabbitmq.message.invalid_json",
                queue=queue_name.queue,
                body_preview=body_preview,
            )
            return None

        if not isinstance(content, dict):
            log.warning(
                "rabbitmq.message.invalid_payload",
                queue=queue_name.queue,
                reason="not_a_json_object",
            )
            return None

        event = content.get("event")
        if not event:
            log.warning(
                "rabbitmq.message.missing_event",
                queue=queue_name.queue,
                payload_preview=content,
            )
            return None

        payload = content.get("payload", content.get("data"))
        return QueueEvent(
            event=str(event), payload=payload, queue=queue_name.queue, raw=content
        )
