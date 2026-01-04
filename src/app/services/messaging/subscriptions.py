from app.core.logging import get_logger
from app.services.events import Event, SSEManager
from app.services.messaging.queues import Queue, subscription_queues
from app.services.messaging.rabbitmq import RabbitMQManager
from app.services.messaging.subscriber import (
    QueueEvent,
    RabbitMQSubscriptionService,
)

log = get_logger(__name__)


class ApplicationSubscriptions(RabbitMQSubscriptionService):
    """Application-specific event handlers wired on top of the base subscriber."""

    def __init__(
        self,
        rabbitmq: RabbitMQManager,
        sse_manager: SSEManager,
        queues: list[Queue] | tuple[Queue, ...] = subscription_queues(),
    ):
        super().__init__(rabbitmq, queues)
        self._sse_manager = sse_manager

        # Register event handlers once at init time
        self.on(Event.INCIDENT_ACK.value, self._forward_to_sse)
        self.on(Event.VEHICLE_ASSIGNMENT_PROPOSAL.value, self._forward_to_sse)

    async def _forward_to_sse(self, message: QueueEvent) -> None:
        await self._sse_manager.notify(
            message.event,
            {
                "queue": message.queue,
                "payload": message.payload,
            },
        )

        log.info(
            "subscription.event.forwarded",
            queue=message.queue,
            event_name=message.event,
        )
