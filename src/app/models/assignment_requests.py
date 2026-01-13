from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.incidents import Incident
    from app.models.operators import Operator


class VehicleAssignmentRequest(Base):
    __tablename__ = "vehicle_assignment_requests"

    incident_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("incidents.incident_id", ondelete="CASCADE"),
        primary_key=True,
    )
    requested_by_operator_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("operators.operator_id", ondelete="SET NULL"),
        nullable=True,
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    incident: Mapped["Incident"] = relationship(
        "Incident",
        passive_deletes=True,
    )
    requested_by: Mapped[Optional["Operator"]] = relationship("Operator")
