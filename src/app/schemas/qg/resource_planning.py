from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import VehicleRequirementRule
from app.schemas.qg.common import QGPhaseTypeRef, QGVehicleTypeRef


class QGRequirement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vehicle_type: QGVehicleTypeRef
    min_quantity: int | None = None
    max_quantity: int | None = None
    mandatory: bool | None = None
    preference_rank: int | None = None


class QGRequirementGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    group_id: UUID
    label: str | None = None
    rule: VehicleRequirementRule
    min_total: int | None = None
    max_total: int | None = None
    priority: int | None = None
    is_hard: bool | None = None
    requirements: list[QGRequirement]


class QGPhaseRequirements(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phase_type: QGPhaseTypeRef
    groups: list[QGRequirementGroup]


class QGVehicleAvailability(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vehicle_type: QGVehicleTypeRef
    available: int
    assigned: int
    total: int


class QGRequirementGap(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vehicle_type: QGVehicleTypeRef
    missing: int
    severity: str


class QGResourcePlanningRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    incident_id: UUID
    phase_requirements: list[QGPhaseRequirements]
    availability: list[QGVehicleAvailability]
    gaps: list[QGRequirementGap]
