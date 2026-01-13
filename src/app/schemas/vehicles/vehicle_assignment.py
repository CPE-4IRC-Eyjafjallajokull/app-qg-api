from datetime import datetime
from uuid import UUID

from app.schemas.base import CreateSchema, ReadSchema, UpdateSchema


class VehicleAssignmentBase:
    vehicle_id: UUID
    incident_phase_id: UUID | None = None
    reinforcement_id: UUID | None = None
    assigned_at: datetime | None = None
    arrived_at: datetime | None = None
    assigned_by_operator_id: UUID | None = None
    validated_at: datetime | None = None
    validated_by_operator_id: UUID | None = None
    unassigned_at: datetime | None = None
    notes: str | None = None


class VehicleAssignmentCreate(VehicleAssignmentBase, CreateSchema):
    pass


class VehicleAssignmentUpdate(UpdateSchema):
    incident_phase_id: UUID | None = None
    reinforcement_id: UUID | None = None
    assigned_at: datetime | None = None
    arrived_at: datetime | None = None
    validated_at: datetime | None = None
    unassigned_at: datetime | None = None
    assigned_by_operator_id: UUID | None = None


class VehicleAssignmentRead(VehicleAssignmentBase, ReadSchema):
    vehicle_assignment_id: UUID
