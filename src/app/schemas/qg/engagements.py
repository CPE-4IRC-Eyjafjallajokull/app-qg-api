from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.qg.common import QGPhaseTypeRef, QGVehicleSummary


class QGVehicleAssignmentDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vehicle_assignment_id: UUID
    vehicle_id: UUID
    incident_phase_id: UUID
    assigned_at: datetime
    assigned_by_operator_id: UUID | None = None
    validated_at: datetime | None = None
    validated_by_operator_id: UUID | None = None
    unassigned_at: datetime | None = None
    notes: str | None = None
    vehicle: QGVehicleSummary
    phase_type: QGPhaseTypeRef | None = None


class QGIncidentEngagementsRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    incident_id: UUID
    vehicle_assignments: list[QGVehicleAssignmentDetail]
