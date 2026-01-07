from enum import StrEnum


class Event(StrEnum):
    """Declared application events."""

    NEW_INCIDENT = "new_incident"
    INCIDENT_ACK = "incident_ack"
    VEHICLE_ASSIGNMENT_PROPOSAL = "vehicle_assignment_proposal"
    VEHICLE_POSITION_UPDATE = "vehicle_position_update"
    VEHICLE_STATUS_UPDATE = "vehicle_status_update"


ALL_EVENTS: tuple[Event, ...] = tuple(Event)
