from app.schemas.base import ReadSchema
from app.schemas.incidents.incident import IncidentRead
from app.schemas.qg.common import QGIncidentPhaseRef


class QGIncidentRead(IncidentRead, ReadSchema):
    phases: list[QGIncidentPhaseRef] = []
