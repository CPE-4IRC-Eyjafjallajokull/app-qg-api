from enum import Enum


class Direction(str, Enum):
    SUB = "sub"
    PUB = "pub"


class Queue(Enum):
    """Central registry of RabbitMQ queues and their directions."""

    SDMIS_API = ("sdmis_api", Direction.SUB)
    SDMIS_ENGINE = ("sdmis_engine", Direction.PUB)
    VEHICLE_TELEMETRY = ("vehicle_telemetry", Direction.SUB)
    VEHICLE_ASSIGNMENTS = ("vehicle_assignments", Direction.PUB)
    INCIDENT_TELEMETRY = ("incident_telemetry", Direction.SUB)

    def __init__(self, queue: str, direction: Direction):
        self._queue = queue
        self._direction = direction

    @property
    def queue(self) -> str:
        return self._queue

    @property
    def direction(self) -> Direction:
        return self._direction

    def is_subscription(self) -> bool:
        return self._direction is Direction.SUB

    def is_publication(self) -> bool:
        return self._direction is Direction.PUB


def subscription_queues() -> tuple[Queue, ...]:
    """Queues consumed by this service."""
    return tuple(q for q in Queue if q.is_subscription())


def publication_queues() -> tuple[Queue, ...]:
    """Queues the API publishes to."""
    return tuple(q for q in Queue if q.is_publication())


def subscription_names() -> tuple[str, ...]:
    """Convenience list of queue names (str) for broker clients (subs)."""
    return tuple(q.queue for q in subscription_queues())


def publication_names() -> tuple[str, ...]:
    """Convenience list of queue names (str) for broker clients (pubs)."""
    return tuple(q.queue for q in publication_queues())
