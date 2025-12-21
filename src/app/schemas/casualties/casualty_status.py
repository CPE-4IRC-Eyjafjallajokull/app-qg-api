from uuid import UUID

from app.schemas.base import CreateSchema, ReadSchema, UpdateSchema


class CasualtyStatusBase:
    label: str
    reported_in_care_transporting_delivered_deceased: str | None = None


class CasualtyStatusCreate(CasualtyStatusBase, CreateSchema):
    pass


class CasualtyStatusUpdate(UpdateSchema):
    label: str | None = None
    reported_in_care_transporting_delivered_deceased: str | None = None


class CasualtyStatusRead(CasualtyStatusBase, ReadSchema):
    casualty_status_id: UUID
