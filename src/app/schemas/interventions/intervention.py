from datetime import datetime
from uuid import UUID

from app.schemas.base import CreateSchema, ReadSchema, UpdateSchema


class InterventionBase:
    incident_id: UUID
    created_by_operator_id: UUID | None = None
    validated_by_operator_id: UUID | None = None
    validated_at: datetime | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    notes: str | None = None


class InterventionCreate(InterventionBase, CreateSchema):
    pass


class InterventionUpdate(UpdateSchema):
    incident_id: UUID | None = None
    created_by_operator_id: UUID | None = None
    validated_by_operator_id: UUID | None = None
    validated_at: datetime | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    notes: str | None = None


class InterventionRead(InterventionBase, ReadSchema):
    intervention_id: UUID
    created_at: datetime
