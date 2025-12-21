from uuid import UUID

from app.schemas.base import CreateSchema, ReadSchema, UpdateSchema


class CasualtyTypeBase:
    code: str | None = None
    label: str | None = None


class CasualtyTypeCreate(CasualtyTypeBase, CreateSchema):
    pass


class CasualtyTypeUpdate(UpdateSchema):
    code: str | None = None
    label: str | None = None


class CasualtyTypeRead(CasualtyTypeBase, ReadSchema):
    casualty_type_id: UUID
