from uuid import UUID

from app.schemas.base import CreateSchema, ReadSchema, UpdateSchema


class EnergyBase:
    label: str


class EnergyCreate(EnergyBase, CreateSchema):
    pass


class EnergyUpdate(UpdateSchema):
    label: str | None = None


class EnergyRead(EnergyBase, ReadSchema):
    energy_id: UUID
