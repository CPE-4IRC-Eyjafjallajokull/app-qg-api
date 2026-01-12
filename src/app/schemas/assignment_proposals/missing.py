from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.base import CreateSchema, ReadSchema, UpdateSchema


class VehicleAssignmentProposalMissingBase:
    incident_phase_id: UUID
    vehicle_type_id: UUID
    missing_quantity: int = Field(ge=0)


class VehicleAssignmentProposalMissingCreate(
    VehicleAssignmentProposalMissingBase, CreateSchema
):
    pass


class VehicleAssignmentProposalMissingUpdate(UpdateSchema):
    missing_quantity: int | None = Field(default=None, ge=0)


class VehicleAssignmentProposalMissingRead(
    VehicleAssignmentProposalMissingBase, ReadSchema
):
    proposal_id: UUID
    created_at: datetime
