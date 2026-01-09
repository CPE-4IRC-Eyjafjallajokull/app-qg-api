from uuid import UUID

from pydantic import Field

from app.schemas.base import CreateSchema, ReadSchema, UpdateSchema


class ReinforcementVehicleRequestBase:
    reinforcement_id: UUID
    vehicle_type_id: UUID
    quantity: int = Field(..., gt=0)
    assigned_quantity: int = Field(default=0, ge=0)


class ReinforcementVehicleRequestCreate(ReinforcementVehicleRequestBase, CreateSchema):
    pass


class ReinforcementVehicleRequestUpdate(UpdateSchema):
    quantity: int | None = Field(None, gt=0)
    assigned_quantity: int | None = Field(None, ge=0)


class ReinforcementVehicleRequestRead(ReinforcementVehicleRequestBase, ReadSchema):
    pass
