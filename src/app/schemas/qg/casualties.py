from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class QGCasualtyTypeRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    casualty_type_id: UUID
    code: str | None = None
    label: str | None = None


class QGCasualtyStatusRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    casualty_status_id: UUID
    label: str


class QGCasualtyTransportRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    casualty_transport_id: UUID
    vehicle_assignment_id: UUID | None = None
    picked_up_at: datetime | None = None
    dropped_off_at: datetime | None = None
    picked_up_latitude: float | None = None
    picked_up_longitude: float | None = None
    dropped_off_latitude: float | None = None
    dropped_off_longitude: float | None = None
    notes: str | None = None


class QGCasualtyDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    casualty_id: UUID
    incident_phase_id: UUID
    casualty_type: QGCasualtyTypeRef
    casualty_status: QGCasualtyStatusRef
    reported_at: datetime | None = None
    notes: str | None = None
    transports: list[QGCasualtyTransportRead]


class QGCasualtyStatusCount(BaseModel):
    model_config = ConfigDict(extra="forbid")

    casualty_status_id: UUID
    label: str
    count: int


class QGCasualtyStats(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int
    by_status: list[QGCasualtyStatusCount]


class QGCasualtiesRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    incident_id: UUID
    casualties: list[QGCasualtyDetail]
    stats: QGCasualtyStats
