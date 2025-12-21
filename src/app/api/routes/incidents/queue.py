import asyncio
import json
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status

from app.api.dependencies import (
    get_current_user,
    get_rabbitmq_manager,
    get_sse_manager,
)
from app.core.security import AuthenticatedUser
from app.services.events import Event, SSEManager
from app.services.messaging.queues import Queue
from app.services.messaging.rabbitmq import RabbitMQManager

router = APIRouter()


@router.post("/new")
async def new_incident(
    payload: dict[str, Any] = Body(..., description="Incident payload to enqueue"),
    rabbitmq: RabbitMQManager = Depends(get_rabbitmq_manager),
    user: AuthenticatedUser = Depends(get_current_user),
    sse_manager: SSEManager = Depends(get_sse_manager),
) -> dict[str, str]:
    envelope = {
        "event": Event.NEW_INCIDENT.value,
        "payload": {
            "incident": payload,
            "submitted_by": user.username or user.subject,
            "status": "enqueued",
        },
    }
    # Preserve legacy top-level fields for downstream consumers that do not use `event`.
    envelope.update(envelope["payload"])
    message = json.dumps(envelope).encode()

    try:
        await rabbitmq.enqueue(Queue.SDMIS_ENGINE, message, timeout=5.0)
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Message broker unavailable",
        ) from None

    await sse_manager.notify(Event.NEW_INCIDENT.value, envelope["payload"])

    return {"message": "New incident created and enqueued"}
