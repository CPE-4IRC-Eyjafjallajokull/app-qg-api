from datetime import datetime
from uuid import UUID

from app.models.enums import VehicleRequirementRule
from app.schemas.base import CreateSchema, ReadSchema, UpdateSchema


class PhaseTypeVehicleRequirementGroupBase:
    phase_type_id: UUID
    label: str | None = None
    rule: VehicleRequirementRule
    min_total: int | None = None
    max_total: int | None = None
    priority: int | None = None
    is_hard: bool | None = None


class PhaseTypeVehicleRequirementGroupCreate(
    PhaseTypeVehicleRequirementGroupBase, CreateSchema
):
    pass


class PhaseTypeVehicleRequirementGroupUpdate(UpdateSchema):
    phase_type_id: UUID | None = None
    label: str | None = None
    rule: VehicleRequirementRule | None = None
    min_total: int | None = None
    max_total: int | None = None
    priority: int | None = None
    is_hard: bool | None = None


class PhaseTypeVehicleRequirementGroupRead(
    PhaseTypeVehicleRequirementGroupBase, ReadSchema
):
    group_id: UUID
    created_at: datetime
