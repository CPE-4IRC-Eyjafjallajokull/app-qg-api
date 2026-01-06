from uuid import UUID

from app.schemas.base import CreateSchema, ReadSchema, UpdateSchema
from app.schemas.vehicles.vehicle_type import VehicleTypeRead


class VehicleBase:
    vehicle_type_id: UUID
    immatriculation: str
    energy_id: UUID | None = None
    energy_level: float | None = None
    base_interest_point_id: UUID | None = None
    status_id: UUID | None = None


class VehicleCreate(VehicleBase, CreateSchema):
    pass


class VehicleUpdate(UpdateSchema):
    vehicle_type_id: UUID | None = None
    immatriculation: str | None = None
    energy_id: UUID | None = None
    energy_level: float | None = None
    base_interest_point_id: UUID | None = None
    status_id: UUID | None = None


class VehicleRead(VehicleBase, ReadSchema):
    vehicle_id: UUID
    vehicle_type: VehicleTypeRead
