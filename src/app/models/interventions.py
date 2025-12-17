from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Index, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from .incidents import Incident
    from .operators import Operator
    from .vehicles import VehicleAssignment


class Intervention(Base):
    __tablename__ = "interventions"
    __table_args__ = (
        Index("ix_interventions_incident", "incident_id"),
        Index("ix_interventions_created_at", "created_at"),
        Index("ix_interventions_started_at", "started_at"),
        Index("ix_interventions_ended_at", "ended_at"),
    )

    intervention_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    incident_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("incidents.incident_id", ondelete="CASCADE"),
        nullable=False,
    )
    created_by_operator_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("operators.operator_id", ondelete="SET NULL"),
        nullable=True,
    )
    validated_by_operator_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("operators.operator_id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    validated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    incident: Mapped["Incident"] = relationship(
        "Incident", back_populates="interventions", passive_deletes=True
    )
    created_by_operator: Mapped[Optional["Operator"]] = relationship(
        "Operator",
        foreign_keys=[created_by_operator_id],
        back_populates="interventions_created",
    )
    validated_by_operator: Mapped[Optional["Operator"]] = relationship(
        "Operator",
        foreign_keys=[validated_by_operator_id],
        back_populates="interventions_validated",
    )
    vehicle_assignments: Mapped[list["VehicleAssignment"]] = relationship(
        "VehicleAssignment",
        back_populates="intervention",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
