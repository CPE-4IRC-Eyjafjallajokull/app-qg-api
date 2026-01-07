from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.base import CreateSchema, ReadSchema, UpdateSchema
from app.schemas.routing.route import LineStringGeometry


class VehicleAssignmentProposalItemBase:
    incident_phase_id: UUID
    vehicle_id: UUID
    proposal_rank: int = Field(ge=1)
    distance_km: float = Field(ge=0)
    estimated_time_min: int = Field(ge=0)
    route_geometry: LineStringGeometry
    energy_level: float = Field(ge=0, le=1)
    score: float = Field(ge=0, le=1)
    rationale: str | None = None


class VehicleAssignmentProposalItemCreate(
    VehicleAssignmentProposalItemBase, CreateSchema
):
    pass


class VehicleAssignmentProposalItemUpdate(UpdateSchema):
    proposal_rank: int | None = Field(default=None, ge=1)
    distance_km: float | None = Field(default=None, ge=0)
    estimated_time_min: int | None = Field(default=None, ge=0)
    route_geometry: LineStringGeometry | None = None
    energy_level: float | None = Field(default=None, ge=0, le=1)
    score: float | None = Field(default=None, ge=0, le=1)
    rationale: str | None = None


class VehicleAssignmentProposalItemRead(VehicleAssignmentProposalItemBase, ReadSchema):
    proposal_id: UUID
    created_at: datetime
