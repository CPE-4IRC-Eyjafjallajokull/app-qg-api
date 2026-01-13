from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class QGVehicleTypeRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vehicle_type_id: UUID
    code: str
    label: str | None = None


class QGPhaseTypeRef(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    phase_type_id: UUID
    code: str
    label: str | None = None


class QGVehicleAssignmentRef(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    vehicle_assignment_id: UUID
    vehicle_id: UUID
    incident_phase_id: UUID | None = None
    assigned_at: datetime
    arrived_at: datetime | None = None
    assigned_by_operator_id: UUID | None = None
    validated_at: datetime | None = None
    validated_by_operator_id: UUID | None = None
    unassigned_at: datetime | None = None


class QGIncidentPhaseRef(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    incident_phase_id: UUID
    phase_type: QGPhaseTypeRef
    priority: int
    started_at: datetime | None = None
    ended_at: datetime | None = None
    vehicle_assignments: list["QGVehicleAssignmentRef"] = []


class QGVehicleSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vehicle_id: UUID
    immatriculation: str
    vehicle_type: QGVehicleTypeRef
