from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.base import CreateSchema
from app.schemas.incidents.incident import IncidentRead
from app.schemas.incidents.incident_phase import IncidentPhaseRead


class IncidentDeclarationLocation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    address: str
    zipcode: str
    city: str
    latitude: float
    longitude: float


class IncidentDeclarationPhase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phase_type_id: UUID
    priority: int | None = None


class IncidentDeclarationCreate(CreateSchema):
    location: IncidentDeclarationLocation
    description: str | None = None
    created_by_operator_id: UUID | None = None
    incident_started_at: datetime | None = None
    phase: IncidentDeclarationPhase


class IncidentDeclarationRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    incident: IncidentRead
    initial_phase: IncidentPhaseRead
