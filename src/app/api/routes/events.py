from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.api.dependencies import authorize_events, get_sse_manager
from app.core.logging import get_logger
from app.services.events import SSEManager

router = APIRouter()
log = get_logger(__name__)


@router.get("/events")
async def events_stream(
    sse_manager: SSEManager = Depends(get_sse_manager),
    _=Depends(authorize_events),
    events: list[str] | None = Query(
        default=None,
        description="Optional list of event names to subscribe to",
        alias="events",
    ),
):
    """
    Server-sent events stream for one-way, real-time updates.

    This endpoint provides:
    - Real-time internal events broadcast through the SSE manager
    - Optional filtering by event name via the `events` query parameter
    - Automatic heartbeat to keep connections alive
    - Graceful disconnection handling
    """
    return StreamingResponse(
        sse_manager.event_stream(events=events),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )
