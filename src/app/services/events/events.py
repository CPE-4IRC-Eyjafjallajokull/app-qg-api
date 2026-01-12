from enum import StrEnum


class Event(StrEnum):
    """Declared application events."""

    NEW_INCIDENT = "new_incident"
    INCIDENT_ACK = "incident_ack"
    INCIDENT_STATUS_UPDATE = "incident_status_update"
    INCIDENT_PHASE_UPDATE = "incident_phase_update"
    VEHICLE_ASSIGNMENT_PROPOSAL_REQUEST = "vehicle_assignment_proposal_request"
    VEHICLE_ASSIGNMENT_PROPOSAL = "vehicle_assignment_proposal"
    VEHICLE_ASSIGNMENT = "vehicle_assignment"
    VEHICLE_POSITION_UPDATE = "vehicle_position_update"
    VEHICLE_STATUS_UPDATE = "vehicle_status_update"


ALL_EVENTS: tuple[Event, ...] = tuple(Event)
