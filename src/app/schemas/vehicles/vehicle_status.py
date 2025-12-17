from uuid import UUID

from app.schemas.base import CreateSchema, ReadSchema, UpdateSchema


class VehicleStatusBase:
    label: str


class VehicleStatusCreate(VehicleStatusBase, CreateSchema):
    pass


class VehicleStatusUpdate(UpdateSchema):
    label: str | None = None


class VehicleStatusRead(VehicleStatusBase, ReadSchema):
    vehicle_status_id: UUID
