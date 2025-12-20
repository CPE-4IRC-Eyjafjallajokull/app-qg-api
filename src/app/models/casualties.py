from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DOUBLE_PRECISION, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from .incidents import IncidentPhase
    from .vehicles import VehicleAssignment


class Casualty(Base):
    __tablename__ = "casualties"
    __table_args__ = (
        Index("ix_casualties_incident_phase", "incident_phase_id"),
        Index("ix_casualties_status", "casualty_status_id"),
    )

    casualty_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    incident_phase_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("incident_phases.incident_phase_id", ondelete="CASCADE"),
        nullable=False,
    )
    casualty_type_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("casualty_types.casualty_type_id", ondelete="CASCADE"),
        nullable=False,
    )
    casualty_status_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("casualty_status.casualty_status_id", ondelete="CASCADE"),
        nullable=False,
    )
    reported_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    incident_phase: Mapped["IncidentPhase"] = relationship(
        "IncidentPhase", back_populates="casualties", passive_deletes=True
    )
    casualty_type: Mapped["CasualtyType"] = relationship(
        "CasualtyType", back_populates="casualties"
    )
    status: Mapped["CasualtyStatus"] = relationship(
        "CasualtyStatus", back_populates="casualties"
    )
    transports: Mapped[list["CasualtyTransport"]] = relationship(
        "CasualtyTransport",
        back_populates="casualty",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class CasualtyType(Base):
    __tablename__ = "casualty_types"

    casualty_type_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    label: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    casualties: Mapped[list[Casualty]] = relationship(
        "Casualty",
        back_populates="casualty_type",
        passive_deletes=True,
    )


class CasualtyStatus(Base):
    __tablename__ = "casualty_status"

    casualty_status_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    label: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    reported_in_care_transporting_delivered_deceased: Mapped[Optional[str]] = (
        mapped_column(String, nullable=True)
    )

    casualties: Mapped[list[Casualty]] = relationship(
        "Casualty",
        back_populates="status",
        passive_deletes=True,
    )


class CasualtyTransport(Base):
    __tablename__ = "casualty_transports"
    __table_args__ = (
        Index("ix_casualty_transports_casualty", "casualty_id"),
        Index("ix_casualty_transports_vehicle_assignment", "vehicle_assignment_id"),
    )

    casualty_transport_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    casualty_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("casualties.casualty_id", ondelete="CASCADE"),
        nullable=False,
    )
    vehicle_assignment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("vehicle_assignments.vehicle_assignment_id", ondelete="SET NULL"),
        nullable=True,
    )
    picked_up_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    dropped_off_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    picked_up_latitude: Mapped[Optional[float]] = mapped_column(
        DOUBLE_PRECISION, nullable=True
    )
    picked_up_longitude: Mapped[Optional[float]] = mapped_column(
        DOUBLE_PRECISION, nullable=True
    )
    dropped_off_latitude: Mapped[Optional[float]] = mapped_column(
        DOUBLE_PRECISION, nullable=True
    )
    dropped_off_longitude: Mapped[Optional[float]] = mapped_column(
        DOUBLE_PRECISION, nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    casualty: Mapped[Casualty] = relationship(
        "Casualty", back_populates="transports", passive_deletes=True
    )
    vehicle_assignment: Mapped[Optional["VehicleAssignment"]] = relationship(
        "VehicleAssignment", back_populates="casualty_transports"
    )
