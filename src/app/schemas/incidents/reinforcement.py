from datetime import datetime
from uuid import UUID

from app.schemas.base import CreateSchema, ReadSchema, UpdateSchema


class ReinforcementBase:
    incident_phase_id: UUID
    validated_at: datetime | None = None
    rejected_at: datetime | None = None
    notes: str | None = None


class ReinforcementCreate(ReinforcementBase, CreateSchema):
    pass


class ReinforcementUpdate(UpdateSchema):
    incident_phase_id: UUID | None = None
    validated_at: datetime | None = None
    rejected_at: datetime | None = None
    notes: str | None = None


class ReinforcementRead(ReinforcementBase, ReadSchema):
    reinforcement_id: UUID
    created_at: datetime
