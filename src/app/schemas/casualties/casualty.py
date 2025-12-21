from datetime import datetime
from uuid import UUID

from app.schemas.base import CreateSchema, ReadSchema, UpdateSchema


class CasualtyBase:
    incident_phase_id: UUID
    casualty_type_id: UUID
    casualty_status_id: UUID
    reported_at: datetime | None = None
    notes: str | None = None


class CasualtyCreate(CasualtyBase, CreateSchema):
    pass


class CasualtyUpdate(UpdateSchema):
    incident_phase_id: UUID | None = None
    casualty_type_id: UUID | None = None
    casualty_status_id: UUID | None = None
    reported_at: datetime | None = None
    notes: str | None = None


class CasualtyRead(CasualtyBase, ReadSchema):
    casualty_id: UUID
