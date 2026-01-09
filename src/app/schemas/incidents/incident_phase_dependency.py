from datetime import datetime
from uuid import UUID

from app.models.enums import IncidentPhaseDependencyKind
from app.schemas.base import CreateSchema, ReadSchema, UpdateSchema


class IncidentPhaseDependencyBase:
    incident_phase_id: UUID
    depends_on_incident_phase_id: UUID
    kind: IncidentPhaseDependencyKind


class IncidentPhaseDependencyCreate(IncidentPhaseDependencyBase, CreateSchema):
    pass


class IncidentPhaseDependencyUpdate(UpdateSchema):
    incident_phase_id: UUID | None = None
    depends_on_incident_phase_id: UUID | None = None
    kind: IncidentPhaseDependencyKind | None = None


class IncidentPhaseDependencyRead(IncidentPhaseDependencyBase, ReadSchema):
    created_at: datetime
