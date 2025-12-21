from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.schemas.base import CreateSchema, ReadSchema, UpdateSchema


class InterestPointConsumableBase:
    interest_point_id: UUID
    interest_point_consumable_type_id: UUID
    current_quantity: Decimal | None = None
    last_update: datetime | None = None


class InterestPointConsumableCreate(InterestPointConsumableBase, CreateSchema):
    pass


class InterestPointConsumableUpdate(UpdateSchema):
    current_quantity: Decimal | None = None
    last_update: datetime | None = None


class InterestPointConsumableRead(InterestPointConsumableBase, ReadSchema):
    pass
