from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from .incidents import Incident
    from .vehicles import VehicleAssignment


class Operator(Base):
    __tablename__ = "operators"

    operator_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, unique=True, index=True
    )

    incidents_created: Mapped[list["Incident"]] = relationship(
        "Incident", back_populates="created_by", passive_deletes=True
    )
    vehicle_assignments_made: Mapped[list["VehicleAssignment"]] = relationship(
        "VehicleAssignment",
        back_populates="assigned_by_operator",
        foreign_keys="VehicleAssignment.assigned_by_operator_id",
        passive_deletes=True,
    )
