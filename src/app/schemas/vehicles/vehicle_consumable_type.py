from uuid import UUID

from app.schemas.base import CreateSchema, ReadSchema, UpdateSchema


class VehicleConsumableTypeBase:
    label: str
    unit: str | None = None


class VehicleConsumableTypeCreate(VehicleConsumableTypeBase, CreateSchema):
    pass


class VehicleConsumableTypeUpdate(UpdateSchema):
    label: str | None = None
    unit: str | None = None


class VehicleConsumableTypeRead(VehicleConsumableTypeBase, ReadSchema):
    vehicle_consumable_type_id: UUID
