from datetime import datetime
from uuid import UUID

from app.schemas.base import CreateSchema, ReadSchema, UpdateSchema


class IncidentBase:
    created_by_operator_id: UUID | None = None
    address: str | None = None
    zipcode: str | None = None
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    description: str | None = None
    ended_at: datetime | None = None


class IncidentCreate(IncidentBase, CreateSchema):
    pass


class IncidentUpdate(UpdateSchema):
    created_by_operator_id: UUID | None = None
    address: str | None = None
    zipcode: str | None = None
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    description: str | None = None
    ended_at: datetime | None = None


class IncidentRead(IncidentBase, ReadSchema):
    incident_id: UUID
    created_at: datetime
    updated_at: datetime
