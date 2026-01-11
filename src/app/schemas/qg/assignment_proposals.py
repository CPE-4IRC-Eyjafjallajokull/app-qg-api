from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class QGAssignmentProposalRequest(BaseModel):
    incident_id: UUID


class QGProposalItem(BaseModel):
    incident_phase_id: UUID
    vehicle_id: UUID
    distance_km: float
    estimated_time_min: float
    energy_level: float
    score: float
    rationale: str | None = None


class QGAssignmentProposalRead(BaseModel):
    proposal_id: UUID
    incident_id: UUID
    generated_at: datetime
    proposals: list[QGProposalItem]
    missing_by_vehicle_type: dict[UUID, int]
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
