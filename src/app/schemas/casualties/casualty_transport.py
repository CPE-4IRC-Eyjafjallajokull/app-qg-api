from datetime import datetime
from uuid import UUID

from app.schemas.base import CreateSchema, ReadSchema, UpdateSchema


class CasualtyTransportBase:
    casualty_id: UUID
    vehicle_assignment_id: UUID | None = None
    picked_up_at: datetime | None = None
    dropped_off_at: datetime | None = None
    picked_up_latitude: float | None = None
    picked_up_longitude: float | None = None
    dropped_off_latitude: float | None = None
    dropped_off_longitude: float | None = None
    notes: str | None = None


class CasualtyTransportCreate(CasualtyTransportBase, CreateSchema):
    pass


class CasualtyTransportUpdate(UpdateSchema):
    casualty_id: UUID | None = None
    vehicle_assignment_id: UUID | None = None
    picked_up_at: datetime | None = None
    dropped_off_at: datetime | None = None
    picked_up_latitude: float | None = None
    picked_up_longitude: float | None = None
    dropped_off_latitude: float | None = None
    dropped_off_longitude: float | None = None
    notes: str | None = None


class CasualtyTransportRead(CasualtyTransportBase, ReadSchema):
    casualty_transport_id: UUID
