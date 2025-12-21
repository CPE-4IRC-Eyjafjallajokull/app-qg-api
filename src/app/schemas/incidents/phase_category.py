from uuid import UUID

from app.schemas.base import CreateSchema, ReadSchema, UpdateSchema


class PhaseCategoryBase:
    code: str
    label: str | None = None


class PhaseCategoryCreate(PhaseCategoryBase, CreateSchema):
    pass


class PhaseCategoryUpdate(UpdateSchema):
    code: str | None = None
    label: str | None = None


class PhaseCategoryRead(PhaseCategoryBase, ReadSchema):
    phase_category_id: UUID
