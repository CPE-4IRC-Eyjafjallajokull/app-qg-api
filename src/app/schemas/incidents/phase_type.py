from uuid import UUID

from app.schemas.base import CreateSchema, ReadSchema, UpdateSchema


class PhaseTypeBase:
    phase_category_id: UUID
    code: str
    label: str | None = None
    default_criticality: int


class PhaseTypeCreate(PhaseTypeBase, CreateSchema):
    pass


class PhaseTypeUpdate(UpdateSchema):
    phase_category_id: UUID | None = None
    code: str | None = None
    label: str | None = None
    default_criticality: int | None = None


class PhaseTypeRead(PhaseTypeBase, ReadSchema):
    phase_type_id: UUID
