from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.base import ReadSchema
from app.schemas.incidents.incident import IncidentRead
from app.schemas.qg.common import QGIncidentPhaseRef


class QGIncidentPhaseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phase_type_id: UUID
    priority: int = 0
    started_at: datetime | None = None
    ended_at: datetime | None = None


class QGIncidentRead(IncidentRead, ReadSchema):
    phases: list[QGIncidentPhaseRef] = []
