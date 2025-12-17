from pydantic import BaseModel, ConfigDict


class CreateSchema(BaseModel):
    """Base class for write/create payloads."""

    model_config = ConfigDict(extra="forbid")


class UpdateSchema(BaseModel):
    """Base class for partial update payloads."""

    model_config = ConfigDict(extra="forbid")


class ReadSchema(BaseModel):
    """Base class for read models (ORM -> response)."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")
