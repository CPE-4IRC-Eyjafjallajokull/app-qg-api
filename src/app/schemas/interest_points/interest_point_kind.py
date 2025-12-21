from uuid import UUID

from app.schemas.base import CreateSchema, ReadSchema, UpdateSchema


class InterestPointKindBase:
    label: str


class InterestPointKindCreate(InterestPointKindBase, CreateSchema):
    pass


class InterestPointKindUpdate(UpdateSchema):
    label: str | None = None


class InterestPointKindRead(InterestPointKindBase, ReadSchema):
    interest_point_kind_id: UUID
