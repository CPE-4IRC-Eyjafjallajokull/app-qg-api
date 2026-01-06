from datetime import datetime
from uuid import UUID

from app.schemas.base import CreateSchema, ReadSchema, UpdateSchema
from app.schemas.incidents.incident import IncidentRead
from app.schemas.incidents.phase_type import PhaseTypeRead


class IncidentPhaseBase:
    incident_id: UUID
    phase_type_id: UUID
    priority: int = 0
    started_at: datetime | None = None
    ended_at: datetime | None = None


class IncidentPhaseCreate(IncidentPhaseBase, CreateSchema):
    pass


class IncidentPhaseUpdate(UpdateSchema):
    incident_id: UUID | None = None
    phase_type_id: UUID | None = None
    priority: int | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None


class IncidentPhaseRead(IncidentPhaseBase, ReadSchema):
    incident_phase_id: UUID
    phase_type: PhaseTypeRead
    incident: IncidentRead
