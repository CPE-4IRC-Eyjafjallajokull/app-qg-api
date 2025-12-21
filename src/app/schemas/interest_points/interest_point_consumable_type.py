from uuid import UUID

from app.schemas.base import CreateSchema, ReadSchema, UpdateSchema


class InterestPointConsumableTypeBase:
    label: str


class InterestPointConsumableTypeCreate(InterestPointConsumableTypeBase, CreateSchema):
    pass


class InterestPointConsumableTypeUpdate(UpdateSchema):
    label: str | None = None


class InterestPointConsumableTypeRead(InterestPointConsumableTypeBase, ReadSchema):
    interest_point_consumable_type_id: UUID
