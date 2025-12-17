from uuid import UUID

from app.schemas.base import CreateSchema, ReadSchema, UpdateSchema


class VehicleTypeBase:
    code: str
    label: str


class VehicleTypeCreate(VehicleTypeBase, CreateSchema):
    pass


class VehicleTypeUpdate(UpdateSchema):
    code: str | None = None
    label: str | None = None


class VehicleTypeRead(VehicleTypeBase, ReadSchema):
    vehicle_type_id: UUID
