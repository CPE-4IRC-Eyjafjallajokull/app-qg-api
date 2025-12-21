from uuid import UUID

from app.schemas.base import CreateSchema, ReadSchema, UpdateSchema


class CasualtyStatusBase:
    label: str


class CasualtyStatusCreate(CasualtyStatusBase, CreateSchema):
    pass


class CasualtyStatusUpdate(UpdateSchema):
    label: str | None = None


class CasualtyStatusRead(CasualtyStatusBase, ReadSchema):
    casualty_status_id: UUID
