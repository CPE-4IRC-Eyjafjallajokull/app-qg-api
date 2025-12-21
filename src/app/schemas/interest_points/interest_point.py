from uuid import UUID

from app.schemas.base import CreateSchema, ReadSchema, UpdateSchema


class InterestPointBase:
    name: str | None = None
    address: str | None = None
    zipcode: str | None = None
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    interest_point_kind_id: UUID | None = None


class InterestPointCreate(InterestPointBase, CreateSchema):
    pass


class InterestPointUpdate(UpdateSchema):
    name: str | None = None
    address: str | None = None
    zipcode: str | None = None
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    interest_point_kind_id: UUID | None = None


class InterestPointRead(InterestPointBase, ReadSchema):
    interest_point_id: UUID
