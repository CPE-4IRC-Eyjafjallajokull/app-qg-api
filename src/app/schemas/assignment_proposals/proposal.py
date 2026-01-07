from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.schemas.assignment_proposals.item import VehicleAssignmentProposalItemRead
from app.schemas.assignment_proposals.missing import (
    VehicleAssignmentProposalMissingRead,
)
from app.schemas.base import CreateSchema, ReadSchema, UpdateSchema


class VehicleAssignmentProposalCreate(CreateSchema):
    proposal_id: UUID
    incident_id: UUID
    generated_at: datetime
    received_at: datetime | None = None


class VehicleAssignmentProposalUpdate(UpdateSchema):
    generated_at: datetime | None = None
    received_at: datetime | None = None


class VehicleAssignmentProposalRead(ReadSchema):
    proposal_id: UUID
    incident_id: UUID
    generated_at: datetime
    received_at: datetime
    items: list[VehicleAssignmentProposalItemRead] = []
    missing: list[VehicleAssignmentProposalMissingRead] = []
