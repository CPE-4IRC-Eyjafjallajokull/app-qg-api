import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.core.logging import get_logger

router = APIRouter()
log = get_logger(__name__)


@router.get("/events")
async def events_stream():
    """Server-sent events stream for one-way, real-time updates."""

    async def event_source():
        log.info("events.connected", env=settings.environment)
        try:
            yield f"data: {json.dumps({'event': 'connected', 'timestamp': datetime.now(timezone.utc).isoformat()})}\n\n"  # noqa: E501
            while True:
                payload = {
                    "event": "heartbeat",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                yield f"data: {json.dumps(payload)}\n\n"
                await asyncio.sleep(settings.events_ping_interval_seconds)
        except asyncio.CancelledError:
            log.info("events.disconnected")
            raise

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )
