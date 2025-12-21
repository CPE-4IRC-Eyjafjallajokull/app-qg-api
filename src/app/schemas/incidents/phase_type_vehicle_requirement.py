from datetime import datetime
from uuid import UUID

from app.schemas.base import CreateSchema, ReadSchema, UpdateSchema


class PhaseTypeVehicleRequirementBase:
    group_id: UUID
    vehicle_type_id: UUID
    min_quantity: int | None = None
    max_quantity: int | None = None
    mandatory: bool | None = None
    preference_rank: int | None = None


class PhaseTypeVehicleRequirementCreate(PhaseTypeVehicleRequirementBase, CreateSchema):
    pass


class PhaseTypeVehicleRequirementUpdate(UpdateSchema):
    min_quantity: int | None = None
    max_quantity: int | None = None
    mandatory: bool | None = None
    preference_rank: int | None = None


class PhaseTypeVehicleRequirementRead(PhaseTypeVehicleRequirementBase, ReadSchema):
    created_at: datetime
