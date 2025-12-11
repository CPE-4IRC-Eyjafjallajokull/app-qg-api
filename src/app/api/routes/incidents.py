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
from app.services.events import SSEManager
from app.services.events.constants import INCIDENT_DECLARED_EVENT, NEW_INCIDENT_QUEUE
from app.services.messaging.rabbitmq import RabbitMQManager

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.post("/new")
async def new_incident(
    payload: dict[str, Any] = Body(..., description="Incident payload to enqueue"),
    rabbitmq: RabbitMQManager = Depends(get_rabbitmq_manager),
    user: AuthenticatedUser = Depends(get_current_user),
    sse_manager: SSEManager = Depends(get_sse_manager),
) -> dict[str, str]:
    message = json.dumps(
        {
            "incident": payload,
            "submitted_by": user.username or user.subject,
        }
    ).encode()

    try:
        await rabbitmq.enqueue(NEW_INCIDENT_QUEUE, message, timeout=5.0)
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Message broker unavailable",
        ) from None

    await sse_manager.notify(
        INCIDENT_DECLARED_EVENT,
        {
            "incident": payload,
            "submitted_by": user.username or user.subject,
            "status": "enqueued",
        },
    )

    return {"message": "New incident created and enqueued"}
