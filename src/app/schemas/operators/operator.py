from uuid import UUID

from app.schemas.base import CreateSchema, ReadSchema, UpdateSchema


class OperatorBase:
    email: str | None = None


class OperatorCreate(OperatorBase, CreateSchema):
    pass


class OperatorUpdate(UpdateSchema):
    email: str | None = None


class OperatorRead(OperatorBase, ReadSchema):
    operator_id: UUID
