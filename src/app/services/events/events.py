from enum import StrEnum


class Event(StrEnum):
    """Declared application events."""

    NEW_INCIDENT = "new_incident"
    INCIDENT_ACK = "incident_ack"
    VEHICLE_ASSIGNMENT_PROPOSAL = "vehicle_assignment_proposal"


ALL_EVENTS: tuple[Event, ...] = tuple(Event)
