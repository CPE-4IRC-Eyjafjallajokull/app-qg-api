import asyncio
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Iterable, Optional

from app.core.logging import get_logger

log = get_logger(__name__)

EventPayload = dict[str, Any]


@dataclass
class _Subscriber:
    queue: asyncio.Queue[Optional[EventPayload]]
    topics: Optional[frozenset[str]]
    kind: str = "stream"  # "stream" for SSE, "listener" for internal subscribers

    def accepts(self, event: str) -> bool:
        return self.topics is None or event in self.topics


class SSEManager:
    """
    Central event hub for the API.

    - Internal producers call `notify(event, data)` to emit an event.
    - Internal consumers can iterate over `listen(...)` to react to events.
    - SSE clients use `event_stream(...)` to receive SSE-formatted messages.
    """

    def __init__(self, heartbeat_interval: float = 30.0, queue_size: int = 100):
        self._subscribers: list[_Subscriber] = []
        self._heartbeat_interval = heartbeat_interval
        self._queue_size = queue_size
        self._lock = asyncio.Lock()

    @property
    def client_count(self) -> int:
        """Return the number of connected SSE clients (stream subscribers)."""
        return sum(1 for sub in self._subscribers if sub.kind == "stream")

    async def notify(self, event: str, data: Any) -> None:
        """
        Emit an event to all subscribers.

        Example:
            await sse_manager.notify("new_incident", {"id": 123})
        """
        message = self._build_message(event, data)
        await self._fan_out(message)

    async def listen(
        self, events: Iterable[str] | None = None
    ) -> AsyncIterator[EventPayload]:
        """
        Subscribe to raw events (internal usage).

        Yields event dictionaries shaped as:
            {"event": <name>, "data": <payload>, "timestamp": <iso8601>}
        """
        subscriber = await self._register_subscriber(events, kind="listener")

        try:
            while True:
                message = await subscriber.queue.get()
                if message is None:
                    break
                yield message
        finally:
            await self._unregister_subscriber(subscriber)

    async def event_stream(
        self, events: Iterable[str] | None = None
    ) -> AsyncIterator[str]:
        """
        SSE-friendly stream for HTTP clients.

        Sends a connected event immediately, heartbeats when idle, and forwards any
        notified events matching the optional `events` filter.
        """
        subscriber = await self._register_subscriber(events, kind="stream")
        topics = sorted(subscriber.topics) if subscriber.topics else ["all"]
        log.info("sse.client.connected", topics=topics, total_clients=self.client_count)

        try:
            yield self._format_sse(self._build_message("connected", {"topics": topics}))

            while True:
                try:
                    message = await asyncio.wait_for(
                        subscriber.queue.get(), timeout=self._heartbeat_interval
                    )
                except asyncio.TimeoutError:
                    yield self._format_sse(
                        self._build_message(
                            "heartbeat",
                            {"topics": topics},
                        )
                    )
                    continue

                if message is None:
                    break

                yield self._format_sse(message)

        except asyncio.CancelledError:
            log.info("sse.client.cancelled")
            raise
        finally:
            await self._unregister_subscriber(subscriber)
            log.info(
                "sse.client.disconnected",
                topics=topics,
                total_clients=self.client_count,
            )

    async def disconnect_all(self) -> None:
        """Disconnect all subscribers gracefully."""
        async with self._lock:
            subscribers = list(self._subscribers)

        for subscriber in subscribers:
            try:
                subscriber.queue.put_nowait(None)
            except asyncio.QueueFull:
                pass

        async with self._lock:
            self._subscribers.clear()

        log.info("sse.all_clients.disconnected")

    async def _register_subscriber(
        self,
        events: Iterable[str] | None,
        kind: str,
    ) -> _Subscriber:
        topics = frozenset(events) if events else None
        subscriber = _Subscriber(
            queue=asyncio.Queue(self._queue_size),
            topics=topics,
            kind=kind,
        )

        # Mutex on subscriber list because its a shared resource
        async with self._lock:
            self._subscribers.append(subscriber)

        return subscriber

    async def _unregister_subscriber(self, subscriber: _Subscriber) -> None:
        async with self._lock:
            if subscriber in self._subscribers:
                self._subscribers.remove(subscriber)

    async def _fan_out(self, message: EventPayload) -> None:
        async with self._lock:
            subscribers = list(self._subscribers)

        event_name = message.get("event", "message")
        for subscriber in subscribers:
            if not subscriber.accepts(event_name):
                continue

            try:
                subscriber.queue.put_nowait(message)
            except asyncio.QueueFull:
                log.warning(
                    "sse.queue.full",
                    event_name=event_name,
                    kind=subscriber.kind,
                )

    @staticmethod
    def _build_message(event: str, data: Any) -> EventPayload:
        return {
            "event": event,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def _format_sse(message: EventPayload) -> str:
        """Format data as an SSE message (standard event + data lines)."""
        event_name = message.get("event", "message")
        return f"event: {event_name}\ndata: {json.dumps(message, default=str)}\n\n"
