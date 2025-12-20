from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.schemas.base import CreateSchema, ReadSchema, UpdateSchema


class VehicleConsumableStockBase:
    vehicle_id: UUID
    consumable_type_id: UUID
    current_quantity: Decimal | None = None


class VehicleConsumableStockCreate(VehicleConsumableStockBase, CreateSchema):
    pass


class VehicleConsumableStockUpdate(UpdateSchema):
    current_quantity: Decimal | None = None


class VehicleConsumableStockRead(VehicleConsumableStockBase, ReadSchema):
    last_update: datetime
