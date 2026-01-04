from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.incidents import IncidentRead
from app.schemas.qg.common import QGVehicleTypeRef


class QGIncidentSnapshot(IncidentRead):
    status: str


class QGPhaseDependency(BaseModel):
    model_config = ConfigDict(extra="forbid")

    depends_on_incident_phase_id: UUID
    kind: str


class QGActivePhase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    incident_phase_id: UUID
    incident_id: UUID
    phase_type_id: UUID
    phase_code: str
    phase_label: str | None = None
    priority: int | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    dependencies: list[QGPhaseDependency] = []


class QGResourcesByType(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vehicle_type: QGVehicleTypeRef
    count: int


class QGResourcesSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vehicles_assigned: int
    vehicles_active: int
    by_type: list[QGResourcesByType]


class QGCasualtyStatusCount(BaseModel):
    model_config = ConfigDict(extra="forbid")

    casualty_status_id: UUID
    label: str
    count: int


class QGCasualtiesSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int
    by_status: list[QGCasualtyStatusCount]


class QGIncidentSituationRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    incident: QGIncidentSnapshot
    phases_active: list[QGActivePhase]
    resources: QGResourcesSummary
    casualties: QGCasualtiesSummary
