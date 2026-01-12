from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class QGAssignmentProposalRequest(BaseModel):
    incident_phase_id: UUID
    vehicles: list["QGAssignmentProposalRequestVehicle"]


class QGAssignmentProposalRequestVehicle(BaseModel):
    vehicle_type_id: UUID
    qty: int = Field(ge=1)


class QGProposalVehicle(BaseModel):
    incident_phase_id: UUID
    vehicle_id: UUID
    distance_km: float
    estimated_time_min: float
    energy_level: float
    score: float
    rank: int = Field(ge=1)


class QGProposalMissing(BaseModel):
    incident_phase_id: UUID
    vehicle_type_id: UUID
    missing_quantity: int = Field(ge=0)


class QGAssignmentProposalRead(BaseModel):
    proposal_id: UUID
    incident_id: UUID
    generated_at: datetime
    vehicles_to_send: list[QGProposalVehicle]
    missing: list[QGProposalMissing]
    validated_at: datetime | None = None
    rejected_at: datetime | None = None


class QGAssignmentProposalsListRead(BaseModel):
    assignment_proposals: list[QGAssignmentProposalRead]
    total: int


class QGValidateProposalResponse(BaseModel):
    proposal_id: UUID
    incident_id: UUID
    validated_at: datetime
    assignments_created: int


class QGRejectProposalResponse(BaseModel):
    proposal_id: UUID
    incident_id: UUID
    rejected_at: datetime
