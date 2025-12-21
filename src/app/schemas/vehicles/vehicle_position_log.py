from datetime import datetime
from uuid import UUID

from app.schemas.base import CreateSchema, ReadSchema


class VehiclePositionLogBase:
    vehicle_id: UUID
    latitude: float
    longitude: float
    timestamp: datetime | None = None


class VehiclePositionLogCreate(VehiclePositionLogBase, CreateSchema):
    pass


class VehiclePositionLogRead(VehiclePositionLogBase, ReadSchema):
    vehicle_position_id: UUID
