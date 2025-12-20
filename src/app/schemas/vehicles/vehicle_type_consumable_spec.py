from decimal import Decimal
from uuid import UUID

from app.schemas.base import CreateSchema, ReadSchema, UpdateSchema


class VehicleTypeConsumableSpecBase:
    vehicle_type_id: UUID
    consumable_type_id: UUID
    capacity_quantity: Decimal | None = None
    initial_quantity: Decimal | None = None
    is_applicable: bool | None = None


class VehicleTypeConsumableSpecCreate(VehicleTypeConsumableSpecBase, CreateSchema):
    pass


class VehicleTypeConsumableSpecUpdate(UpdateSchema):
    capacity_quantity: Decimal | None = None
    initial_quantity: Decimal | None = None
    is_applicable: bool | None = None


class VehicleTypeConsumableSpecRead(VehicleTypeConsumableSpecBase, ReadSchema):
    pass
