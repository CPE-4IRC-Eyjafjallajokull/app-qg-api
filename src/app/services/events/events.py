from enum import StrEnum


class Event(StrEnum):
    """Declared application events."""

    NEW_INCIDENT = "new_incident"
    INCIDENT_ACK = "incident_ack"


ALL_EVENTS: tuple[Event, ...] = tuple(Event)
