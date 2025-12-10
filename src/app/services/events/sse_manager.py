import asyncio
import json
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Optional

from app.core.logging import get_logger

log = get_logger(__name__)


class SSEManager:
    """
    Manages Server-Sent Events connections and message broadcasting.

    This class is designed for async environments and allows:
    - Multiple concurrent SSE clients
    - Broadcasting messages to all connected clients
    - Integration with RabbitMQ for receiving external events
    """

    def __init__(self, heartbeat_interval: float = 30.0):
        self._clients: set[asyncio.Queue[Optional[dict[str, Any]]]] = set()
        self._heartbeat_interval = heartbeat_interval
        self._lock = asyncio.Lock()

    @property
    def client_count(self) -> int:
        """Return the number of connected clients."""
        return len(self._clients)

    async def subscribe(self) -> AsyncIterator[str]:
        """
        Subscribe to SSE events. Yields formatted SSE messages.

        Usage:
            async for message in sse_manager.subscribe():
                yield message
        """
        queue: asyncio.Queue[Optional[dict[str, Any]]] = asyncio.Queue()

        async with self._lock:
            self._clients.add(queue)

        log.info("sse.client.connected", total_clients=len(self._clients))

        try:
            # Send initial connection event
            yield self._format_sse(
                {
                    "event": "connected",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

            while True:
                try:
                    # Wait for message with timeout for heartbeat
                    message = await asyncio.wait_for(
                        queue.get(), timeout=self._heartbeat_interval
                    )

                    if message is None:
                        # None signals client should disconnect
                        break

                    yield self._format_sse(message)

                except asyncio.TimeoutError:
                    # Send heartbeat
                    yield self._format_sse(
                        {
                            "event": "heartbeat",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )

        except asyncio.CancelledError:
            log.info("sse.client.cancelled")
            raise
        finally:
            async with self._lock:
                self._clients.discard(queue)
            log.info("sse.client.disconnected", total_clients=len(self._clients))

    async def broadcast(self, event: str, data: Any) -> None:
        """
        Broadcast an event to all connected SSE clients.

        Args:
            event: The event type/name
            data: The data payload (will be JSON serialized)
        """
        message = {
            "event": event,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        async with self._lock:
            for queue in self._clients:
                try:
                    queue.put_nowait(message)
                except asyncio.QueueFull:
                    log.warning("sse.queue.full", event=event)

    async def publish(self, message: dict[str, Any]) -> None:
        """
        Publish a pre-formatted message to all connected SSE clients.

        Args:
            message: The message dict to broadcast
        """
        if "timestamp" not in message:
            message["timestamp"] = datetime.now(timezone.utc).isoformat()

        async with self._lock:
            for queue in self._clients:
                try:
                    queue.put_nowait(message)
                except asyncio.QueueFull:
                    log.warning("sse.queue.full", message=message)

    async def disconnect_all(self) -> None:
        """Disconnect all SSE clients gracefully."""
        async with self._lock:
            for queue in self._clients:
                try:
                    queue.put_nowait(None)
                except asyncio.QueueFull:
                    pass
            self._clients.clear()
        log.info("sse.all_clients.disconnected")

    @staticmethod
    def _format_sse(data: dict[str, Any]) -> str:
        """Format data as an SSE message."""
        return f"data: {json.dumps(data)}\n\n"
